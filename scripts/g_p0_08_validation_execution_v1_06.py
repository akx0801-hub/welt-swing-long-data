"""G-P0-08/v1.06 governed validation execution contract.
Reproduction requires governed v0.53 SQLite SHA bccca4f...07afc and frozen candidate CSV semantic SHA 8148c0...6235.
No provider access. Market reads are hard-filtered day <= 2026-06-08.
"""
VALIDATION_START="2026-03-12"; VALIDATION_END="2026-06-08"; EXPECTED_BASE=64050
HORIZONS=(5,10,15)
def tri_or(a,b):
    if a=="TRUE" or b=="TRUE": return "TRUE"
    if a=="FALSE" and b=="FALSE": return "FALSE"
    return "NOT_VERIFIED_INPUT"
def candidate_status(base_or_stage2,trend,compression,pivot,climax,runup):
    vals=(base_or_stage2,trend,compression,pivot,climax,runup)
    if "NOT_VERIFIED_INPUT" in vals: return "VALIDATION_CANDIDATE_NOT_VERIFIED_INPUT"
    if "FALSE" in (base_or_stage2,trend,compression,pivot) or climax=="TRUE" or runup=="TRUE":
        return "VALIDATION_CANDIDATE_FALSE"
    return "VALIDATION_CANDIDATE_HIT"
def prior_high20_excl_t(high, i): return max(high[i-20:i])
def forward_close_return(close,i,h): return close[i+h]/close[i]-1
def forward_max_pivot_extension_atr(high,i,h,pivot,atr): return (max(high[i+1:i+h+1])-pivot)/atr
def forward_max_drawdown_atr(low,close,i,h,atr): return (min(low[i+1:i+h+1])-close[i])/atr
def forward_any_close_above_anchor_pivot(close,i,h,pivot): return any(x>pivot for x in close[i+1:i+h+1])
