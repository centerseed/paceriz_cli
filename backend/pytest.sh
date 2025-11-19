#!/bin/bash

# Show usage
show_usage() {
    echo "Usage: $0 {dev|prod} [options] [test_file]"
    echo "Options:"
    echo "  --coverage       Generate detailed coverage reports"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev                              # Run all tests"
    echo "  $0 dev --coverage                   # Run tests with coverage"
    echo "  $0 dev tests/test_admin_auth.py     # Run specific test file"
    exit 1
}

# Check if environment is provided
if [ -z "$1" ]; then
    show_usage
fi

# Check for help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_usage
fi

# Check environment argument
if [ "$1" != "dev" ] && [ "$1" != "prod" ]; then
    show_usage
fi

# Initialize variables
COVERAGE=false
TEST_PATH=""
PYTEST_ARGS="-v -s" # Basic pytest arguments

# Parse arguments
ENV=$1
shift # Shift past the environment argument

while [ "$#" -gt 0 ]; do
    case "$1" in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --help|-h)
            show_usage
            ;;
        *)
            if [ -z "$TEST_PATH" ]; then
                TEST_PATH="$1"
            else
                echo "Error: Multiple test paths specified."
                show_usage
            fi
            shift
            ;;
    esac
done

# 根據環境設定 GCP 專案 ID
if [ "$ENV" = "dev" ]; then
    PROJECT_ID="havital-dev"
else
    PROJECT_ID="paceriz-prod"
fi

# 儲存目前的 GCP 專案設定
ORIGINAL_PROJECT=$(gcloud config get-value project 2>/dev/null)
echo "目前 GCP 專案: $ORIGINAL_PROJECT"

# 切換到測試所需的 GCP 專案
echo "切換到測試專案: $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# 設置環境變數
export ENV_TYPE=$ENV
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=0
export SUPER_ADMIN_EMAILS="${SUPER_ADMIN_EMAILS:-centerseedwu@gmail.com}"

# 添加 PYTHONPATH
export PYTHONPATH=$(pwd):$(pwd)/../../../api_service
echo "Setting PYTHONPATH to: $PYTHONPATH"

# 先檢查 pytest 是否已安裝
if ! command -v pytest &> /dev/null; then
    echo "pytest is not installed. Installing now..."
    pip install pytest pytest-cov pytest-mock
fi

# Source conda.sh to make 'conda' command available
if [ -f "/opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh" ]; then
    . "/opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh"
else
    echo "Warning: conda.sh not found. Conda environment might not be activated."
fi

# Handle coverage options
if [ "$COVERAGE" = true ]; then
    echo "Enabling detailed coverage analysis..."
    PYTEST_ARGS="$PYTEST_ARGS --cov=. --cov-report=term --cov-report=html:htmlcov --cov-report=xml:coverage.xml"
fi

# 將環境變數傳遞給 Python
export ENV
export COVERAGE

# Run the tests with verbose output
echo "Running tests with pytest..."
echo "Environment: $ENV_TYPE"
echo "Super Admin: $SUPER_ADMIN_EMAILS"
echo "Pytest args: $PYTEST_ARGS"
echo ""

conda activate api && python -m pytest ${TEST_PATH:-tests/} $PYTEST_ARGS

# 儲存 pytest 的退出碼
PYTEST_EXIT_CODE=$?

# Show coverage summary if coverage was enabled
if [ "$COVERAGE" = true ] && [ $PYTEST_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "=== Coverage Summary ==="
    echo "HTML Coverage Report: htmlcov/index.html"
    echo "XML Coverage Report: coverage.xml"
    echo ""
    echo "To view HTML coverage report, run:"
    echo "open htmlcov/index.html"
fi

# --- 清理環境 ---

# 將 GCP 專案切換回原始設定
if [ ! -z "$ORIGINAL_PROJECT" ]; then
    echo "測試結束，將 GCP 專案切換回: $ORIGINAL_PROJECT..."
    gcloud config set project $ORIGINAL_PROJECT
fi

# 以 pytest 的退出碼退出腳本
exit $PYTEST_EXIT_CODE
