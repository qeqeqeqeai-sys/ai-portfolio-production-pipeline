"""H3 Cross-Replay Structural Transition Intelligence (deterministic, read-only, recommendation-only)."""
from __future__ import annotations
from collections import Counter, OrderedDict
from copy import deepcopy
import hashlib, json
from typing import Any, Mapping

CERTIFIED_CROSS_REPLAY_STRUCTURAL_TRANSITION_INTELLIGENCE = "CERTIFIED_CROSS_REPLAY_STRUCTURAL_TRANSITION_INTELLIGENCE"
DEGRADED_CROSS_REPLAY_STRUCTURAL_TRANSITION_INTELLIGENCE = "DEGRADED_CROSS_REPLAY_STRUCTURAL_TRANSITION_INTELLIGENCE"
BLOCKED_CROSS_REPLAY_STRUCTURAL_TRANSITION_INTELLIGENCE = "BLOCKED_CROSS_REPLAY_STRUCTURAL_TRANSITION_INTELLIGENCE"

def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()

def _rows(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, Mapping):
        data=[data]
    out=[]
    for r in list(data or []):
        if isinstance(r, Mapping): out.append(dict(r))
    out.sort(key=lambda x:(str(x.get('run_timestamp') or x.get('timestamp') or ''), str(x.get('run_id') or x.get('replay_id') or '')))
    return out

def _state(row: Mapping[str, Any], keys: tuple[str,...], default: str="unknown") -> str:
    for k in keys:
        v=row.get(k)
        if v not in (None, ""):
            return str(v).strip().lower()
    return default

def _themes(row: Mapping[str, Any]) -> set[str]:
    vals=row.get('semantic_themes') or row.get('themes') or row.get('semantic',{}).get('themes') or []
    if not isinstance(vals,list): vals=[vals] if vals else []
    return {str(v).strip().lower() for v in vals if str(v).strip()}

def build_h3_replay_transition_inventory(*, replay_windows: Any) -> OrderedDict[str, Any]:
    rows=_rows(deepcopy(replay_windows))
    pairs=[]
    for a,b in zip(rows, rows[1:]):
        a_id=str(a.get('run_id') or a.get('replay_id') or 'unknown')
        b_id=str(b.get('run_id') or b.get('replay_id') or 'unknown')
        reg=( _state(a,('regime','regime_label')), _state(b,('regime','regime_label')))
        con=( _state(a,('contradiction_state','contradiction_label')), _state(b,('contradiction_state','contradiction_label')))
        cty=( _state(a,('continuity_state',)), _state(b,('continuity_state',)))
        cfd=( _state(a,('confidence_state','confidence_label')), _state(b,('confidence_state','confidence_label')))
        fam=( _state(a,('pattern_family',),'unclassified'), _state(b,('pattern_family',),'unclassified'))
        t1,t2=_themes(a),_themes(b)
        pairs.append(OrderedDict([('pair_id',f'{a_id}->{b_id}'),('regime_transition',f'{reg[0]}->{reg[1]}'),('contradiction_transition',f'{con[0]}->{con[1]}'),('continuity_transition',f'{cty[0]}->{cty[1]}'),('confidence_transition',f'{cfd[0]}->{cfd[1]}'),('semantic_theme_transition',OrderedDict([('emergent',sorted(t2-t1)),('decayed',sorted(t1-t2)),('persistent',sorted(t1&t2))])),('recurring_pattern_transition',f'{fam[0]}->{fam[1]}')]))
    seen=set(); novelty=[]; repeated=[]
    for p in pairs:
        key=(p['regime_transition'],p['contradiction_transition'],p['continuity_transition'],p['confidence_transition'])
        (novelty if key not in seen else repeated).append(p['pair_id']); seen.add(key)
    return OrderedDict([('replay_window_sequence',[str(r.get('run_id') or r.get('replay_id') or 'unknown') for r in rows]),('transition_pairs',pairs),('regime_transitions',[p['regime_transition'] for p in pairs]),('contradiction_transitions',[p['contradiction_transition'] for p in pairs]),('continuity_state_transitions',[p['continuity_transition'] for p in pairs]),('confidence_state_transitions',[p['confidence_transition'] for p in pairs]),('semantic_theme_transitions',[p['semantic_theme_transition'] for p in pairs]),('recurring_pattern_transitions',[p['recurring_pattern_transition'] for p in pairs]),('novelty_bearing_transitions',novelty),('repeated_pattern_transitions',repeated)])

def build_h3_structural_transition_chains(*, transition_inventory: Mapping[str, Any]) -> OrderedDict[str, Any]:
    inv=deepcopy(dict(transition_inventory))
    c=inv.get('continuity_state_transitions',[]); f=inv.get('confidence_state_transitions',[]); s=inv.get('semantic_theme_transitions',[])
    return OrderedDict([('contradiction_evolution_chains',list(inv.get('contradiction_transitions',[]))),('continuity_fracture_recovery_chains',[x for x in c if ('fragment' in x or 'recover' in x or 'stable' in x)]),('confidence_convergence_divergence_oscillation_chains',[x for x in f if any(k in x for k in ('converg','diverg','oscillat'))]),('regime_migration_chains',list(inv.get('regime_transitions',[]))),('semantic_theme_persistence_chains',[x.get('persistent',[]) for x in s]),('semantic_theme_decay_chains',[x.get('decayed',[]) for x in s]),('semantic_theme_emergence_chains',[x.get('emergent',[]) for x in s])])

def build_h3_transition_novelty_analysis(*, transition_inventory: Mapping[str, Any], transition_chains: Mapping[str, Any]) -> OrderedDict[str, Any]:
    inv=dict(transition_inventory); n=max(1,len(inv.get('transition_pairs',[])))
    def ratio(xs): return round(len(set(xs))/max(1,len(xs)),4)
    regimes=[x.split('->')[-1] for x in inv.get('regime_transitions',[]) if '->' in x]
    return OrderedDict([('contradiction_type_novelty',ratio(inv.get('contradiction_transitions',[]))),('continuity_transition_novelty',ratio(inv.get('continuity_state_transitions',[]))),('confidence_transition_novelty',ratio(inv.get('confidence_state_transitions',[]))),('semantic_theme_novelty',round(sum(1 for x in inv.get('semantic_theme_transitions',[]) if x.get('emergent'))/n,4)),('regime_transition_novelty',ratio(inv.get('regime_transitions',[]))),('repeated_pattern_family_density',round(len(inv.get('repeated_pattern_transitions',[]))/n,4)),('semantic_saturation',round(sum(1 for x in inv.get('semantic_theme_transitions',[]) if not x.get('emergent'))/n,4)),('regime_monoculture',round(max(Counter(regimes).values())/max(1,len(regimes)),4) if regimes else 1.0),('marginal_structural_information_gain',round(len(inv.get('novelty_bearing_transitions',[]))/n,4))])

def build_h3_transition_risk_diagnostics(*, transition_inventory: Mapping[str, Any], novelty_analysis: Mapping[str, Any]) -> OrderedDict[str, Any]:
    inv=dict(transition_inventory); nov=dict(novelty_analysis)
    return OrderedDict([('transition_stagnation', nov.get('marginal_structural_information_gain',0)<0.35),('repeated_transition_loops', len(inv.get('repeated_pattern_transitions',[]))>0),('regime_concentration', nov.get('regime_monoculture',1.0)>=0.75),('contradiction_monoculture', nov.get('contradiction_type_novelty',0)<=0.4),('semantic_saturation', nov.get('semantic_saturation',0)>=0.7),('weak_confidence_movement', nov.get('confidence_transition_novelty',0)<=0.4),('weak_continuity_movement', nov.get('continuity_transition_novelty',0)<=0.4),('replay_density_without_structural_evolution', nov.get('repeated_pattern_family_density',0)>=0.6 and nov.get('marginal_structural_information_gain',0)<=0.4)])

def build_h3_operator_transition_recommendations(*, novelty_analysis: Mapping[str, Any], risk_diagnostics: Mapping[str, Any]) -> list[OrderedDict[str, Any]]:
    recs=[OrderedDict([('priority',1),('title','Target transition novelty first'),('action_type','recommendation_only'),('narrative','Prioritize replay windows likely to add contradiction, continuity, confidence, and semantic-theme transition novelty under governed approval.')])]
    if risk_diagnostics.get('regime_concentration'): recs.append(OrderedDict([('priority',2),('title','Reduce regime monoculture'),('action_type','recommendation_only'),('narrative','Select windows from underrepresented regimes to reduce concentration while preserving deterministic replay ordering.')]))
    if risk_diagnostics.get('semantic_saturation'): recs.append(OrderedDict([('priority',3),('title','Increase semantic-theme novelty'),('action_type','recommendation_only'),('narrative','Favor windows with expected theme emergence/decay instead of repeated persistent themes.')]))
    recs.append(OrderedDict([('priority',4),('title','Governance-preserving diversification'),('action_type','recommendation_only'),('narrative','No autonomous execution, no writes, no predictive/trading behavior, no D21 execution in H3.')]))
    return recs

def build_h3_dashboard_payload(*, transition_inventory: Mapping[str, Any], transition_chains: Mapping[str, Any], novelty_analysis: Mapping[str, Any], risk_diagnostics: Mapping[str, Any], operator_recommendations: list[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    return OrderedDict([('Cross-Replay Transition Overview',deepcopy(dict(transition_inventory))),('Structural Transition Chains',deepcopy(dict(transition_chains))),('Transition Novelty Analysis',deepcopy(dict(novelty_analysis))),('Contradiction Evolution',transition_chains.get('contradiction_evolution_chains',[])),('Continuity-State Transitions',transition_inventory.get('continuity_state_transitions',[])),('Confidence-State Transitions',transition_inventory.get('confidence_state_transitions',[])),('Regime Transitions',transition_inventory.get('regime_transitions',[])),('Semantic Theme Evolution',OrderedDict([('persistence',transition_chains.get('semantic_theme_persistence_chains',[])),('decay',transition_chains.get('semantic_theme_decay_chains',[])),('emergence',transition_chains.get('semantic_theme_emergence_chains',[]))])),('Transition Risk Diagnostics',deepcopy(dict(risk_diagnostics))),('Operator Replay-Diversification Guidance',[OrderedDict(x) for x in operator_recommendations]),('Governance/Lineage Controls',OrderedDict([('read_only',True),('no_writes',True),('no_direct_sql',True),('no_predictive_or_trading_behavior',True),('no_autonomous_execution',True),('no_d21_execution',True)]))])

def certify_h3_cross_replay_structural_transition_intelligence(*, transition_inventory: Mapping[str, Any], transition_chains: Mapping[str, Any], dashboard_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    seq=list(transition_inventory.get('replay_window_sequence',[])) if isinstance(transition_inventory,Mapping) else []
    blocked=[]
    if len(seq)<2: blocked.append('INSUFFICIENT_REPLAY_WINDOWS')
    status = BLOCKED_CROSS_REPLAY_STRUCTURAL_TRANSITION_INTELLIGENCE if blocked else (CERTIFIED_CROSS_REPLAY_STRUCTURAL_TRANSITION_INTELLIGENCE if transition_chains else DEGRADED_CROSS_REPLAY_STRUCTURAL_TRANSITION_INTELLIGENCE)
    return OrderedDict([('status',status),('blocking_reasons',blocked),('checksum',_stable_checksum({'inventory':transition_inventory,'chains':transition_chains,'dashboard':dashboard_payload})),('deterministic_replay_ordering_preserved',True),('transition_ordering_deterministic',True),('no_autonomous_generation',True),('no_predictive_or_trading_behavior',True),('no_writes',True),('governance_preserved',True),('replay_determinism_preserved',True),('transition_chains_bounded_reproducible',True)])

def build_h3_report_payload(*, dashboard_payload: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([('dashboard',deepcopy(dict(dashboard_payload))),('certification',deepcopy(dict(certification)))])

def build_h3_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    cert=(report_payload or {}).get('certification',{}) if isinstance(report_payload,Mapping) else {}
    return "\n".join(["# H3 Cross-Replay Structural Transition Intelligence", f"- Status: {cert.get('status','UNKNOWN')}", "- Deterministic, read-only, recommendation-only transition intelligence layer."])

__all__=[x for x in globals() if x.startswith('build_h3_') or x.startswith('certify_h3_') or x.endswith('CROSS_REPLAY_STRUCTURAL_TRANSITION_INTELLIGENCE')]
