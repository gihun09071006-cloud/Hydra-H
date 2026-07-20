# datasets/

The `datasets/` directory is HYDRA's data foundation. It holds the raw and
derived data that the engines learn from and evaluate against. This directory
defines *where data lives*; it contains no data-processing logic.

## Structure

### products/

Raw product information. The source records that describe each product before
any analysis — the input material for the Product Intelligence Engine.

### winning_ads/

Successful advertisements used for learning. Examples of ads that performed
well, kept as positive references for pattern extraction and evaluation.

### failed_ads/

Failed advertisements used for comparison. Examples of ads that underperformed,
kept as negative references so the system can learn what to avoid.

### patterns/

Extracted advertising patterns. The reusable patterns distilled from winning and
failed ads — the learned signal that informs future decisions.

### market_fit/

Historical Market Fit evaluations. A record of past Market Fit Engine outputs,
used to track decisions over time and to calibrate future scoring.
