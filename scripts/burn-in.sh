#!/bin/bash
# Run burn-in loop for flaky test detection

ITERATIONS=${1:-10}

echo "🔥 Running burn-in loop ($ITERATIONS iterations)..."

for i in $(seq 1 $ITERATIONS); do
  echo "Iteration $i/$ITERATIONS"
  npm run test:e2e || exit 1
done

echo "✅ Burn-in passed"
