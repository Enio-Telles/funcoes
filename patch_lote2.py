import re

def main():
    with open("server/python/core/produto_batch_lote.py", "r") as f:
        content = f.read()

    new_func = """def construir_preview_unificacao_lote(
    df_agregados: pl.DataFrame,
    df_pairs: pl.DataFrame,
    rule_ids: list[str],
    source_method: str,
    require_all_pairs_compatible: bool = True,
    max_component_size: int = 12,
) -> dict[str, Any]:
    rows = [normalize_final_group_row(row) for row in df_agregados.to_dicts()]
    row_map = {row["chave_produto"]: row for row in rows if row["chave_produto"] and row["descricao"]}

    pair_lookup, edges_by_rule = _evaluate_all_pairs(df_pairs, row_map, rule_ids)

    proposals: list[dict[str, Any]] = []
    total_components = 0
    claimed_components: set[tuple[str, ...]] = set()

    for rule_id in [rule for rule in RULE_PRIORITY if rule in rule_ids]:
        adjacency: dict[str, set[str]] = defaultdict(set)
        for left_key, right_key in edges_by_rule.get(rule_id, []):
            adjacency[left_key].add(right_key)
            adjacency[right_key].add(left_key)

        components = _find_connected_components(adjacency, max_component_size)

        proposal_index = 1
        for component_keys in components:
            component_signature = tuple(component_keys)
            if component_signature in claimed_components:
                continue

            valid_component, edge_contexts = _validate_and_build_contexts(
                component_keys, rule_id, row_map, pair_lookup, edges_by_rule, require_all_pairs_compatible
            )

            if not valid_component or not edge_contexts:
                continue

            component_rows = [row_map[key] for key in component_keys]
            proposals.append(_build_component_summaries(component_rows, edge_contexts, rule_id, proposal_index, source_method))
            proposal_index += 1
            total_components += 1
            claimed_components.add(component_signature)

    summary_by_rule = _generate_rule_summaries(proposals, rule_ids)

    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "resumo": {
            "total_rows_considered": len(row_map),
            "total_candidate_pairs": int(df_pairs.height),
            "total_components": total_components,
            "total_proposals": len(proposals),
            "by_rule": summary_by_rule,
        },
        "proposals": proposals,
    }
"""

    pattern = r'def construir_preview_unificacao_lote\(.*?\n        "proposals": proposals,\n    \}'
    match = re.search(pattern, content, flags=re.DOTALL)

    if match:
        new_content = content[:match.start()] + new_func + "\n" + content[match.end():]
        with open("server/python/core/produto_batch_lote.py", "w") as f:
            f.write(new_content)
    else:
        print("Function not replaced")

main()
