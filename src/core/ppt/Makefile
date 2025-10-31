# 深度研究平台PPT模块 Makefile

.PHONY: help install install-dev test test-coverage test-unit test-integration lint format type-check clean run-example

# 默认目标
help:
	@echo "深度研究平台PPT模块开发工具"
	@echo ""
	@echo "可用命令:"
	@echo "  install      - 安装生产依赖"
	@echo "  install-dev  - 安装开发依赖"
	@echo "  test         - 运行所有测试"
	@echo "  test-coverage- 运行测试并生成覆盖率报告"
	@echo "  test-unit    - 运行单元测试"
	@echo "  test-integration - 运行集成测试"
	@echo "  lint         - 运行代码检查"
	@echo "  format       - 格式化代码"
	@echo "  type-check   - 类型检查"
	@echo "  clean        - 清理临时文件"
	@echo "  run-example  - 运行示例代码"

# 安装依赖
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pytest-cov pytest-mypy

# 测试相关
test:
	pytest tests/ -v

test-coverage:
	pytest tests/ --cov=src --cov-report=html --cov-report=term

test-unit:
	pytest tests/ -m "not integration" -v

test-integration:
	pytest tests/ -m "integration" -v

# 代码质量
lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

type-check:
	mypy src/

# 清理
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# 示例代码
run-example:
	python -c "
import asyncio
import sys
sys.path.append('../../../')
from src.core.ppt.generator import create_presentation

async def main():
    try:
        params = {
            'title': '技术演示',
            'outline': ['引言', '核心技术', '应用案例', '总结'],
            'n_slides': 4,
            'language': 'Chinese',
            'tone': 'professional'
        }
        result = await create_presentation(params)
        print(f'PPT生成成功: {result[\"path\"]}')
    except Exception as e:
        print(f'生成失败: {e}')

asyncio.run(main())
"

# 开发环境检查
check-dev: format type-check lint test
	@echo "开发环境检查完成！"

# 发布准备
prep-release: clean format type-check lint test-coverage
	@echo "发布准备完成！"