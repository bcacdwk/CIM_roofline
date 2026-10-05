"""Component services plus explicit event-scheduled volatile maintenance.
Frozen P1 aggregate is called unchanged; no old result files are imported.
"""
import math
from service import aggregate as aggregate_serial

def aggregate(resolved,model):
    maintenance=model.get('maintenance')
    if maintenance is not None:
        if not isinstance(maintenance,dict) or maintenance.get('basis')!='actual_event_schedule' or not isinstance(maintenance.get('feasible'),bool):
            raise ValueError('Explicit event-schedule maintenance contract required')
        required=('raw_stream_s','raw_resident_s','retention_limit_s')
        optional=('long_term_stream_interval_s','long_term_resident_interval_s','single_admitted_stream_latency_s','single_resident_post_refresh_latency_s','max_group_writeback_gap_s')
        fields=required+optional
        for key in fields:
            value=maintenance.get(key)
            if value is None and key in optional and not maintenance['feasible']:continue
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:raise ValueError('Invalid maintenance field '+key)
        if not maintenance.get('schedule_policy') or not maintenance.get('event_summary'):raise ValueError('Maintenance policy and actual event summary required')
        feasible=maintenance['feasible'] and maintenance['max_group_writeback_gap_s']<=maintenance['retention_limit_s']
        model['physical_checks'].append({'id':'actual_refresh_schedule_feasible','passed':feasible,'critical':True,'evidence':maintenance['event_summary']})
    result=aggregate_serial(resolved,model)
    if maintenance is None:return result
    if not math.isclose(result['delta_S_raw_s'],maintenance['raw_stream_s'],rel_tol=1e-9,abs_tol=1e-15) or not math.isclose(result['resident_s'],maintenance['raw_resident_s'],rel_tol=1e-9,abs_tol=1e-15):raise ValueError('Maintenance raw service disagrees with staged work')
    ds=maintenance['long_term_stream_interval_s'];tr=maintenance['long_term_resident_interval_s']
    if (ds is not None and ds+1e-15<maintenance['raw_stream_s']) or (tr is not None and tr+1e-15<maintenance['raw_resident_s']):raise ValueError('Maintenance creates free service capacity')
    result['maintenance_basis']='actual event schedule; volatile state, refresh payload zero'
    result['maintenance']=maintenance
    result['raw_rho_MB_per_s']=result['B_S_Byte']/maintenance['raw_stream_s']/1e6
    result['raw_tau_MB_per_s']=result['B_R_Byte']/maintenance['raw_resident_s']/1e6
    result['resident_raw_s']=result['resident_s']
    result['single_latency_s']=maintenance['single_admitted_stream_latency_s']
    result['single_resident_latency_s']=maintenance['single_resident_post_refresh_latency_s']
    result['resident_s']=maintenance['single_resident_post_refresh_latency_s']
    result['delta_S_effective_s']=ds;result['resident_effective_interval_s']=tr
    if result['status'] in ('valid','conditional'):
        rho=result['B_S_Byte']/ds;tau=result['B_R_Byte']/tr
        result.update(rho_MB_per_s=rho/1e6,tau_MB_per_s=tau/1e6,RI_star=rho/tau,U_star=tr/ds)
    return result
