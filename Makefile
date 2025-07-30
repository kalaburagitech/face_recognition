# Makefile for Face Recognition System

.PHONY: help install dev start test format lint clean

help:  ## 显示帮助信息
	@echo "Face Recognition System - Makefile"
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## 安装依赖 (使用 uv)
	@echo "Installing dependencies with uv..."
	uv venv --python 3.12
	uv pip install -e .

install-dev:  ## 安装开发依赖
	@echo "Installing development dependencies..."
	uv pip install -e ".[dev]"

dev:  ## 启动开发服务器 (热重载)
	@echo "Starting development server..."
	python main.py --reload

start:  ## 启动生产服务器
	@echo "Starting production server..."
	python main.py

test:  ## 运行测试
	@echo "Running tests..."
	pytest tests/ -v

format:  ## 格式化代码
	@echo "Formatting code..."
	black src/ tests/
	isort src/ tests/

lint:  ## 代码检查
	@echo "Running linters..."
	flake8 src/ tests/
	mypy src/

type-check:  ## 类型检查
	@echo "Running type checks..."
	mypy src/

docs:  ## 生成文档
	@echo "API documentation available at:"
	@echo "  Swagger UI: http://localhost:8000/docs"
	@echo "  ReDoc:      http://localhost:8000/redoc"

clean:  ## 清理临时文件
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

demo:  ## 运行演示
	@echo "Running demo..."
	python demo.py

cli-help:  ## 显示CLI工具帮助
	@echo "CLI tool help:"
	face-recognition --help

setup:  ## 初始化项目 (首次运行)
	@echo "Setting up project..."
	mkdir -p data/database data/faces data/uploads logs
	uv venv --python 3.12
	uv pip install -e .
	@echo "Setup complete! Run 'make dev' to start development server."

# 数据库相关
db-init:  ## 初始化数据库
	@echo "Initializing database..."
	python -c "from src.models.database import DatabaseManager; DatabaseManager()"

db-stats:  ## 显示数据库统计
	@echo "Database statistics:"
	face-recognition stats

# 示例命令
example-enroll:  ## 示例：人脸入库
	@echo "Example: Face enrollment"
	@echo "face-recognition enroll -d data/faces/张三 -n '张三' -desc '员工'"

example-predict:  ## 示例：人脸识别
	@echo "Example: Face recognition"
	@echo "face-recognition predict -i test.jpg"

# 性能测试
benchmark:  ## 简单性能测试
	@echo "Running benchmark..."
	@echo "This will test API response times..."
	curl -X GET "http://localhost:8000/api/health" -w "\nResponse time: %{time_total}s\n"

# 安全检查
security:  ## 安全检查
	@echo "Running security checks..."
	pip-audit

# 构建
build:  ## 构建项目
	@echo "Building project..."
	python -m build

# 部署相关
docker-build:  ## 构建 Docker 镜像
	@echo "Building Docker image..."
	docker build -t face-recognition-system .

docker-run:  ## 运行 Docker 容器
	@echo "Running Docker container..."
	docker run -p 8000:8000 face-recognition-system
