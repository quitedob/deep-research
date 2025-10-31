# -*- coding: utf-8 -*-
"""
计费服务：Stripe 集成，包括订阅创建、管理门户和 Webhook 处理。
"""

from __future__ import annotations

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from src.core.db import get_db_session
from src.sqlmodel.models import User, Subscription
from src.services.auth_service import get_current_user
from src.services.billing_service import BillingService
from src.config.loader.config_loader import get_settings
from src.api.errors import create_error_response, ErrorCodes, handle_database_error, handle_not_found_error

# 初始化 Stripe
settings = get_settings()
if STRIPE_AVAILABLE and settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutSessionResp(BaseModel):
    """创建 Checkout 会话响应"""
    url: str


class PortalSessionResp(BaseModel):
    """创建客户门户会话响应"""
    url: str


class WebhookResp(BaseModel):
    """Webhook 处理响应"""
    status: str


@router.post("/create-checkout-session", response_model=CheckoutSessionResp)
async def create_checkout_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    创建 Stripe Checkout 会话，用于用户订阅 - 通过BillingService处理业务逻辑
    """
    if not STRIPE_AVAILABLE:
        return create_error_response(
            code=ErrorCodes.BUSINESS_LOGIC_ERROR,
            message="支付服务暂时不可用",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    try:
        billing_service = BillingService(db)

        # 检查用户是否已有活跃订阅
        existing_subscription = await billing_service.get_user_subscription(
            user_id=str(current_user.id)
        )
        if existing_subscription:
            return create_error_response(
                code=ErrorCodes.BUSINESS_LOGIC_ERROR,
                message="用户已有活跃订阅",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # 从配置获取 Stripe 价格 ID 和前后端 URL
        price_id = settings.stripe_price_id
        success_url = f"{settings.frontend_url}/subscribe/success"
        cancel_url = f"{settings.frontend_url}/subscribe/canceled"

        # 检查用户是否已有 Stripe 客户 ID
        stripe_customer_id = current_user.stripe_customer_id

        if not stripe_customer_id:
            # 如果用户在 Stripe 中不存在，则创建一个
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.username,
                metadata={'user_id': str(current_user.id)}
            )
            stripe_customer_id = customer.id

            # 更新用户的 Stripe 客户 ID（这里需要通过DAO更新）
            await db.execute(
                update(User)
                .where(User.id == current_user.id)
                .values(stripe_customer_id=stripe_customer_id)
            )
            await db.commit()

        # 创建 Checkout 会话
        checkout_session = stripe.checkout.Session.create(
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            customer=stripe_customer_id,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={'user_id': str(current_user.id)},  # 附加内部用户 ID，便于 Webhook 处理
            allow_promotion_codes=True,
            billing_address_collection='required',
        )

        return CheckoutSessionResp(url=checkout_session.url)

    except stripe.error.StripeError as e:
        return create_error_response(
            code=ErrorCodes.BUSINESS_LOGIC_ERROR,
            message=f"Stripe error: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return handle_database_error(e, "billing_operation")


@router.post("/create-portal-session", response_model=PortalSessionResp)
async def create_portal_session(
    current_user: User = Depends(get_current_user)
):
    """
    创建 Stripe 客户门户会话，用于管理订阅
    """
    if not STRIPE_AVAILABLE:
        return create_error_response(
            code=ErrorCodes.BUSINESS_LOGIC_ERROR,
            message="支付服务暂时不可用",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    try:
        # 从配置加载客户门户返回 URL
        return_url = f"{settings.frontend_url}/settings/subscription"
        
        if not current_user.stripe_customer_id:
            return create_error_response(
                code=ErrorCodes.BUSINESS_LOGIC_ERROR,
                message="用户不是付费客户",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # 创建客户门户会话
        portal_session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=return_url,
        )
        
        return PortalSessionResp(url=portal_session.url)
        
    except stripe.error.StripeError as e:
        return create_error_response(
            code=ErrorCodes.BUSINESS_LOGIC_ERROR,
            message=f"Stripe error: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return handle_database_error(e, "billing_operation")


@router.post("/webhooks/stripe", response_model=WebhookResp)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db_session)
):
    """
    处理来自 Stripe 的 Webhook 事件
    """
    try:
        webhook_secret = settings.stripe_webhook_secret
        payload = await request.body()

        # 验证 Webhook 签名
        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=stripe_signature,
                secret=webhook_secret
            )
        except ValueError as e:
            return create_error_response(
                code=ErrorCodes.VALIDATION_ERROR,
                message="Invalid payload",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except stripe.error.SignatureVerificationError as e:
            return create_error_response(
                code=ErrorCodes.VALIDATION_ERROR,
                message="Invalid signature",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # 处理不同类型的事件
        if event['type'] == 'checkout.session.completed':
            await _handle_checkout_completed(event, db)
        elif event['type'] == 'customer.subscription.updated':
            await _handle_subscription_updated(event, db)
        elif event['type'] == 'customer.subscription.deleted':
            await _handle_subscription_deleted(event, db)
        elif event['type'] == 'invoice.payment_failed':
            await _handle_payment_failed(event, db)
        elif event['type'] == 'invoice.payment_succeeded':
            await _handle_payment_succeeded(event, db)

        return WebhookResp(status="success")
        
    except Exception as e:
        # 记录错误但不返回错误响应，避免 Stripe 重试
        print(f"Webhook error: {str(e)}")
        return WebhookResp(status="error")


async def _handle_checkout_completed(event: dict, db: AsyncSession):
    """处理结账完成事件 - 通过BillingService处理业务逻辑"""
    session = event['data']['object']
    user_id = session['metadata']['user_id']
    stripe_subscription_id = session['subscription']

    try:
        billing_service = BillingService(db)

        # 获取订阅详情
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)

        # 通过服务层创建或更新订阅
        result = await billing_service.create_subscription(
            user_id=user_id,
            stripe_subscription_id=stripe_subscription_id,
            plan_name="Deep Research Pro",
            status=subscription.status,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end
        )

        if result.get("success"):
            logger.info(f"订阅创建成功: {result.get('subscription_id')}")
        else:
            logger.error(f"订阅创建失败: {result.get('error')}")

    except Exception as e:
        logger.error(f"处理结账完成事件失败: {e}")
        # 记录错误但不抛出异常，避免 Stripe 重试


async def _handle_subscription_updated(event: dict, db: AsyncSession):
    """处理订阅更新事件 - 通过BillingService处理业务逻辑"""
    subscription = event['data']['object']

    try:
        billing_service = BillingService(db)

        # 通过服务层更新订阅
        result = await billing_service.update_subscription_from_stripe(
            stripe_subscription_id=subscription.id,
            status=subscription.status,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end
        )

        if result.get("success"):
            logger.info(f"订阅更新成功: {result.get('subscription_id')}")
        else:
            logger.error(f"订阅更新失败: {result.get('error')}")

    except Exception as e:
        logger.error(f"处理订阅更新事件失败: {e}")


async def _handle_subscription_deleted(event: dict, db: AsyncSession):
    """处理订阅删除事件 - 通过BillingService处理业务逻辑"""
    subscription = event['data']['object']

    try:
        billing_service = BillingService(db)

        # 通过服务层取消订阅
        result = await billing_service.update_subscription_from_stripe(
            stripe_subscription_id=subscription.id,
            status='canceled'
        )

        if result.get("success"):
            logger.info(f"订阅删除成功: {result.get('subscription_id')}")
        else:
            logger.error(f"订阅删除失败: {result.get('error')}")

    except Exception as e:
        logger.error(f"处理订阅删除事件失败: {e}")


async def _handle_payment_failed(event: dict, db: AsyncSession):
    """处理支付失败事件 - 通过BillingService处理业务逻辑"""
    invoice = event['data']['object']

    try:
        billing_service = BillingService(db)

        # 通过服务层更新订阅状态
        result = await billing_service.update_subscription_from_stripe(
            stripe_subscription_id=invoice.subscription,
            status='past_due'
        )

        if result.get("success"):
            logger.info(f"支付失败事件处理成功: {result.get('subscription_id')}")
        else:
            logger.error(f"支付失败事件处理失败: {result.get('error')}")

    except Exception as e:
        logger.error(f"处理支付失败事件失败: {e}")


async def _handle_payment_succeeded(event: dict, db: AsyncSession):
    """处理支付成功事件 - 通过BillingService处理业务逻辑"""
    invoice = event['data']['object']

    try:
        billing_service = BillingService(db)

        # 通过服务层更新订阅状态
        result = await billing_service.update_subscription_from_stripe(
            stripe_subscription_id=invoice.subscription,
            status='active'
        )

        if result.get("success"):
            logger.info(f"支付成功事件处理成功: {result.get('subscription_id')}")
        else:
            logger.error(f"支付成功事件处理失败: {result.get('error')}")

    except Exception as e:
        logger.error(f"处理支付成功事件失败: {e}")


@router.get("/subscription-status")
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取当前用户的订阅状态 - 通过BillingService处理业务逻辑
    """
    try:
        billing_service = BillingService(db)

        # 通过服务层获取用户订阅信息
        subscription = await billing_service.get_user_subscription(
            user_id=str(current_user.id)
        )

        if subscription:
            return {
                "has_active_subscription": True,
                "subscription_id": subscription.get("subscription_id"),
                "status": subscription.get("status"),
                "current_period_end": subscription.get("current_period_end"),
                "plan_name": subscription.get("plan_name")
            }
        else:
            return {
                "has_active_subscription": False,
                "subscription_id": None,
                "status": None,
                "current_period_end": None,
                "plan_name": None
            }

    except Exception as e:
        return handle_database_error(e, "获取订阅状态")
