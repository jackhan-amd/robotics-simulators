"""Sequential evidence refresh; legacy report generators are intentionally omitted."""
from workspace import script_command
import argparse,pathlib,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--collect',action='store_true');a=p.parse_args()
B=pathlib.Path(__file__).resolve().parent
steps=(['collect.py']if a.collect else[])+['update_humanizer_review.py','provided_progress.py','publish_provided_images.py','gpu_campaign_audit.py','finalize_gpu_campaign.py','summarize_mjx_failures.py','enforce_gpu_report_scope.py','audit_gpu_measurements.py','finalize_evidence.py','apply_reviewed_prose.py','report_presentation.py','polite_korean.py','render_final.py','audit_artifacts.py']
for step in steps:
 print('REFRESH',step,flush=True)
 subprocess.run(script_command(step),check=True)
