// =========================================================================
// FINPILOT AI — MEASURED BENCHMARK EVALUATION
// =========================================================================

async function runBenchmarkEvaluation() {
  try {
    const res = await apiFetch("/v1/controller/evaluation");
    const data = await res.json();
    renderEvaluationScorecard(data);
    showToast("Benchmark evaluation executed against ground truth!");
  } catch (err) {
    showToast(err.message, true);
  }
}

function renderEvaluationScorecard(evalData) {
  if (!evalData) return;
  const setTxt = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };

  setTxt("evalAccuracy", evalData.match_accuracy !== undefined ? `${evalData.match_accuracy}%` : "N/A");
  setTxt("evalPrecision", evalData.exception_precision !== undefined ? `${evalData.exception_precision}%` : "N/A");
  setTxt("evalRecall", evalData.exception_recall !== undefined ? `${evalData.exception_recall}%` : "N/A");
  setTxt("evalF1Score", evalData.f1_score !== undefined ? `${evalData.f1_score}%` : "N/A");
  setTxt("evalTP", evalData.exceptions_detected !== undefined ? evalData.exceptions_detected : "—");
  setTxt("evalTN", evalData.total_records !== undefined && evalData.exceptions_detected !== undefined ? (evalData.total_records - evalData.exceptions_detected) : "—");
  setTxt("evalFP", evalData.false_positives !== undefined ? evalData.false_positives : "0");
  setTxt("evalFN", evalData.false_negatives !== undefined ? evalData.false_negatives : "0");
  setTxt("evalTotalRecords", evalData.total_records !== undefined ? `${evalData.total_records} Records` : "—");
  setTxt("evalDuration", evalData.execution_time_s !== undefined ? `${evalData.execution_time_s}s` : "—");
  setTxt("evalThroughput", evalData.throughput_rps ? `${Math.round(evalData.throughput_rps).toLocaleString()} records/sec` : "Not measured");
}
