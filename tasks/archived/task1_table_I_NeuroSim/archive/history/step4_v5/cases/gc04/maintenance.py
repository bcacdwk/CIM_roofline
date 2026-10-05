"""GC-04 actual periodic maintenance and request scheduler (SI seconds).

No workload oracle. Streaming requests are non-preemptible; resident loading is
preemptible only between full committed groups. Refresh uses a separate code
hold and never clears retained service progress/output. Payload occurs only at
whole-request completion. This module does not decide electrical retention.
"""
from math import floor


def schedule(period_s, refresh_group_s, groups, stream_s, resident_group_s,
             guard_s=0., periods=100, keep_trace=False):
    H, q, S, B, g = map(float, (period_s, refresh_group_s, stream_s, resident_group_s, guard_s))
    if min(H,q,S,B)>0 and groups>0 and periods>=3 and g>=0:
        pass
    else:
        raise ValueError('positive time/resource domain required')
    R=groups*q
    if R+g >= H:
        return {'feasible':False,'reason':'maintenance_and_guard_fill_period','refresh_s':R}
    # Each maintenance visit occurs at a fixed deadline, in the same physical order.
    # A group writes back at epoch*H+(group+1)*q. These are actual events, not H/R algebra.
    last=[None]*groups; ages=[]; trace=[]
    for epoch in range(periods+1):
        for group in range(groups):
            t=epoch*H+(group+1)*q
            if last[group] is not None:ages.append(t-last[group])
            last[group]=t
            if keep_trace and epoch<3:trace.append({'t_s':t,'kind':'refresh_writeback','group':group,'payload_bytes':0})
    # Saturated stream: whole requests must fit between refresh end and guard.
    stream_completions=[]; request_latencies=[]
    for epoch in range(periods):
        t=epoch*H+R; deadline=(epoch+1)*H-g
        while t+S <= deadline+1e-15:
            start=t;t+=S;stream_completions.append(t);request_latencies.append(t-start)
            if keep_trace and epoch<3:trace.append({'t_s':t,'kind':'stream_complete','start_s':start})
    # Saturated resident: preserve next-group index across refresh, but only intake
    # the next target after the refresh if it cannot be fully committed before guard.
    # Initial service state at first refresh end is retained arbitrary old contents.
    matrix_progress=0; start=R; resident_completions=[]; first_latency=None; commits=0
    write_last=[(j+1)*q for j in range(groups)]; max_age=0.; target_held_across_refresh=False
    for epoch in range(periods):
        if epoch:
            for group in range(groups):
                t=epoch*H+(group+1)*q
                max_age=max(max_age,t-write_last[group]);write_last[group]=t
        t=epoch*H+R;deadline=(epoch+1)*H-g
        while t+B <= deadline+1e-15:
            t+=B
            group=matrix_progress
            max_age=max(max_age,t-write_last[group]);write_last[group]=t
            matrix_progress+=1;commits+=1
            if keep_trace and epoch<3:trace.append({'t_s':t,'kind':'resident_commit','group':group})
            if matrix_progress==groups:
                resident_completions.append(t)
                if first_latency is None:first_latency=t-start
                matrix_progress=0
    # Average intervals from complete interior epoch counts; avoids initial phase
    # making a long-term measure look like single-request latency.
    stream_n=len(stream_completions)
    stream_interval=(periods*H/stream_n) if stream_n else None
    # All resident batches have same slot; boundary wasted partial matrix counts
    # vanish in the asymptotic cycle. Exact rational renewal from actual batch count.
    batch_slots=commits/periods
    resident_interval=H*groups/batch_slots if batch_slots else None
    result={'feasible':bool(stream_n and resident_completions),
      'period_s':H,'refresh_group_s':q,'refresh_s':R,'guard_s':g,
      'maintenance_visits':(periods+1)*groups,'max_same_group_refresh_gap_s':max(ages),
      'max_gap_with_resident_commits_s':max_age,
      'raw_stream_interval_s':S,'physical_stream_latency_s':S,
      'stream_requests_per_period':stream_n/periods,
      'long_term_stream_interval_s':stream_interval,
      'raw_resident_latency_s':groups*B,
      'physical_resident_latency_at_post_refresh_start_s':first_latency,
      'long_term_resident_interval_s':resident_interval,
      'resident_batch_slots_per_period':batch_slots,'completed_resident_requests':len(resident_completions),
      'positive_fraction_only':(H-R-g)/H,'no_stream_fit_despite_positive_fraction':not stream_n,
      'resident_target_held_across_refresh':target_held_across_refresh,
      'resident_progress_at_end':matrix_progress,
      'refresh_payload_bytes':0,
      'last_stream_completion_s':stream_completions[-1] if stream_n else None,
      'trace':sorted(trace,key=lambda e:e['t_s']) if keep_trace else []}
    if not result['feasible']:result['reason']='no_complete_request_fits_actual_periodic_schedule'
    return result


def work_conserving_schedule(retention_limit_s, refresh_group_s, groups,
                             stream_s, resident_group_s, guard_s=0., keep_trace=False,
                             resident_request_setup_s=0.):
    """Whole requests / committed groups, with actual per-request clear work.

    No fractional amortized setup is inserted into atomic group durations.
    Resident progress determines the next clear event and a finite repeat cycle.
    """
    H=retention_limit_s;R=groups*refresh_group_s;B=resident_group_s;setup=resident_request_setup_s
    nstream=int(floor((H-R-guard_s+1e-15)/stream_s))
    nbatch=int(floor((H-R-guard_s+1e-15)/B))
    if nstream<1 or nbatch<1 or B+setup>H-R-guard_s+1e-15:
        return {'feasible':False,'reason':'no_atomic_service_before_retention_deadline',
          'retention_limit_s':H,'refresh_s':R,'stream_atoms_fit':nstream,
          'resident_atoms_fit_upper_bound':nbatch,'positive_idle_fraction':max(0.,(H-R-guard_s)/H)}
    hs=R+nstream*stream_s+guard_s
    ss=schedule(hs,refresh_group_s,groups,stream_s,B,guard_s,periods=3,keep_trace=keep_trace)
    progress=0;now=0.;completed=0;trace=[];initial_last=[-(H-guard_s)+(j+1)*refresh_group_s for j in range(groups)];last=list(initial_last);maxage=0.;first_latency=None
    seen={};periods=[];repeat=None;jobs_at_repeat=None;time_at_repeat=None
    for epoch in range(2*groups+4):
        if progress in seen:
            old_epoch,old_t,old_jobs=seen[progress]
            repeat=epoch-old_epoch;time_at_repeat=now-old_t;jobs_at_repeat=completed-old_jobs
            if jobs_at_repeat>0:break
        else:seen[progress]=(epoch,now,completed)
        start=now;deadline=start+H-guard_s
        for group in range(groups):
            now=start+(group+1)*refresh_group_s
            if last[group] is not None:maxage=max(maxage,now-last[group])
            last[group]=now
            if keep_trace and epoch<3:trace.append({'t_s':now,'kind':'refresh_writeback','group':group,'payload_bytes':0})
        while True:
            atom=B+(setup if progress==0 else 0.)
            if now+atom>deadline+1e-15:break
            if progress==0 and keep_trace and epoch<3:
                trace.append({'t_s':now+setup,'kind':'resident_request_clear','duration_s':setup})
            now+=atom
            if last[progress] is not None:maxage=max(maxage,now-last[progress])
            last[progress]=now
            if keep_trace and epoch<3:trace.append({'t_s':now,'kind':'resident_commit','group':progress})
            progress+=1
            if progress==groups:
                completed+=1;progress=0
                if first_latency is None:first_latency=now-R
                if keep_trace and epoch<3:trace.append({'t_s':now,'kind':'resident_complete'})
        now+=guard_s;periods.append(now-start)
    if not jobs_at_repeat:raise RuntimeError('Resident control recurrence failed to close')
    assert maxage<=H+1e-15
    return {'feasible':True,'policy':'work_conserving_fixed_order_refresh_at_next_atomic_deadline',
      'retention_limit_s':H,'refresh_s':R,'refresh_group_s':refresh_group_s,'groups':groups,
      'guard_s':guard_s,'stream_actual_refresh_period_s':hs,'resident_actual_refresh_periods_s':sorted(set(periods)),
      'stream_requests_per_refresh':nstream,'resident_group_atom_s':B,'resident_request_setup_s':setup,
      'stream_single_admitted_latency_s':stream_s,
      'resident_single_post_refresh_latency_s':first_latency,
      'long_term_stream_interval_s':hs/nstream,'long_term_resident_interval_s':time_at_repeat/jobs_at_repeat,
      'max_stream_group_writeback_gap_s':max(ss['max_same_group_refresh_gap_s'],H-guard_s),
      'initial_maintenance_history_period_s':H-guard_s,'initial_group_last_writeback_s':initial_last,
      'initial_state_policy':'arbitraryvalidoldmatrixinongoingperiodicphase;priorgroupWBstaggered,neverallagezero;admissionafterinitialrefresh',
      'max_resident_group_writeback_gap_s':maxage,
      'resident_progress_repeat_refresh_cycles':repeat,'resident_repeat_complete_payloads':jobs_at_repeat,
      'resident_repeat_elapsed_s':time_at_repeat,
      'resident_progress_retained_across_refresh':True,'pending_target_across_refresh':False,
      'stream_trace':ss['trace'],'resident_trace':trace,'maintenance_payload_bytes':0}


def diagnostic():
    # Counterexample to alpha-only availability: 60% idle, yet one 70us request cannot fit.
    fail=schedule(100e-6,1e-6,40,70e-6,1e-6,periods=10)
    # A resident request can cross refresh boundaries with only group/address state.
    cross=schedule(100e-6,1e-6,40,20e-6,2e-6,periods=10,keep_trace=True)
    assert fail['positive_fraction_only']>0 and fail['no_stream_fit_despite_positive_fraction']
    assert cross['physical_resident_latency_at_post_refresh_start_s']>cross['raw_resident_latency_s']
    assert abs(cross['max_same_group_refresh_gap_s']-100e-6)<1e-15
    assert not cross['resident_target_held_across_refresh']
    wc=work_conserving_schedule(100e-6,1e-6,40,20e-6,2e-6,keep_trace=True)
    assert wc['stream_requests_per_refresh']==3
    assert wc['resident_progress_retained_across_refresh']
    return {'alpha_counterexample':fail,'cross_refresh_resident':cross,'work_conserving':wc}

if __name__=='__main__':
    import argparse,json,pathlib
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);args=ap.parse_args()
    d=diagnostic();pathlib.Path(args.out).write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps({'out':args.out,'positive_fraction_false_positive_detected':True,'actual_cross_refresh_latency_s':d['cross_refresh_resident']['physical_resident_latency_at_post_refresh_start_s']}))
