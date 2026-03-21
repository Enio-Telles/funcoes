import re

def main():
    with open("server/python/core/produto_batch_lote.py", "r") as f:
        content = f.read()

    new_helpers = """
def _evaluate_all_pairs(
    df_pairs, row_map, rule_ids
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, list[tuple[str, str]]]]:
    pair_lookup: dict[tuple[str, str], dict[str, Any]] = {}
    edges_by_rule: dict[str, list[tuple[str, str]]] = {rule_id: [] for rule_id in rule_ids}

    for pair in df_pairs.to_dicts():
        left_key = _clean_text(pair.get("chave_produto_a"))
        right_key = _clean_text(pair.get("chave_produto_b"))
        if not left_key or not right_key or left_key == right_key:
            continue
        left = row_map.get(left_key)
        right = row_map.get(right_key)
        if not left or not right:
            continue
        key = _pair_key(left_key, right_key)
        pair_lookup[key] = _build_pair_context(left, right, pair)
        for rule_id in rule_ids:
            evaluation = evaluate_batch_rule(rule_id, left, right, pair_lookup[key])
            if evaluation.get("eligible"):
                edges_by_rule[rule_id].append(key)

    return pair_lookup, edges_by_rule


def _find_connected_components(adjacency: dict[str, set[str]], max_component_size: int) -> list[list[str]]:
    visited: set[str] = set()
    components: list[list[str]] = []

    for start in sorted(adjacency):
        if start in visited:
            continue
        stack = [start]
        component_keys: list[str] = []
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            component_keys.append(current)
            for neighbor in sorted(adjacency.get(current, set())):
                if neighbor not in visited:
                    stack.append(neighbor)

        component_keys = sorted(set(component_keys))
        if 2 <= len(component_keys) <= max(2, int(max_component_size)):
            components.append(component_keys)

    return components


def _validate_and_build_contexts(
    component_keys: list[str],
    rule_id: str,
    row_map: dict[str, Any],
    pair_lookup: dict[tuple[str, str], dict[str, Any]],
    edges_by_rule: dict[str, list[tuple[str, str]]],
    require_all_pairs_compatible: bool,
) -> tuple[bool, list[dict[str, Any]]]:
    edge_contexts: list[dict[str, Any]] = []
    if require_all_pairs_compatible:
        for left_key, right_key in combinations(component_keys, 2):
            key = _pair_key(left_key, right_key)
            left = row_map[left_key]
            right = row_map[right_key]
            pair_context = pair_lookup.get(key) or _build_pair_context(left, right, None)
            evaluation = evaluate_batch_rule(rule_id, left, right, pair_context)
            if not evaluation.get("eligible"):
                return False, []
            edge_contexts.append(pair_context)
    else:
        for left_key, right_key in edges_by_rule.get(rule_id, []):
            if left_key in component_keys and right_key in component_keys:
                edge_contexts.append(pair_lookup[_pair_key(left_key, right_key)])

    return True, edge_contexts


def _generate_rule_summaries(proposals: list[dict[str, Any]], rule_ids: list[str]) -> list[dict[str, Any]]:
    summary_by_rule: list[dict[str, Any]] = []
    for rule_id in [rule for rule in RULE_PRIORITY if rule in rule_ids]:
        rule_proposals = [item for item in proposals if item["rule_id"] == rule_id]
        grouped_keys = sorted({key for item in rule_proposals for key in item["chaves_produto"]})
        summary_by_rule.append(
            {
                "rule_id": rule_id,
                "button_label": RULE_CONFIG[rule_id]["button_label"],
                "proposal_count": len(rule_proposals),
                "group_count": len(grouped_keys),
            }
        )
    return summary_by_rule
"""

    match = re.search(r'def construir_preview_unificacao_lote\(', content)
    if not match:
        print("Function not found")
        return

    idx = match.start()
    new_content = content[:idx] + new_helpers + "\n\n" + content[idx:]

    with open("server/python/core/produto_batch_lote.py", "w") as f:
        f.write(new_content)

main()
