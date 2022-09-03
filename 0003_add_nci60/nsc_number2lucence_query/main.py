def nsc_number2lucence_query(nsc_number: int):
    query = f"nsc{nsc_number} OR (nsc AND {nsc_number})"

    return query
