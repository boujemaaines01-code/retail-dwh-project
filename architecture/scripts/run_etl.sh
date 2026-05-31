#!/bin/bash
# Run ETL Pipeline

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if dependencies are installed
python -c "import pandas" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip install -r etl/requirements.txt
fi

# Parse arguments
MODE=${1:-initial}
ROWS=${2:-50000}
HOST=${3:-localhost}
PORT=${4:-3306}

echo "Running ETL Pipeline..."
echo "Mode: $MODE"
echo "Rows: $ROWS"
echo "Host: $HOST:$PORT"

# Run ETL
python -m etl.run_etl --mode $MODE --rows $ROWS --host $HOST --port $PORT

if [ $? -eq 0 ]; then
    echo "ETL Pipeline completed successfully!"
else
    echo "ETL Pipeline failed!"
    exit 1
fi
