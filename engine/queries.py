"""
Standard Cypher Query Workloads for Graph Database Cloud Benchmarking.
Evaluates:
- 1-hop traversal
- 2-hop traversal
- 3-hop traversal
- Point lookup (Unindexed / ID lookup)
- Indexed/Filtered lookup
- Aggregations (COUNT / GROUP BY)
- Write workload (Insert relationship/node)
"""

class QueryWorkloads:
    @staticmethod
    def get_1hop_traversal(start_id: int) -> str:
        return f"MATCH (u:User {{id: {start_id}}})-[:FOLLOWS]->(m:User) RETURN m.id AS target_id, m.username AS username"

    @staticmethod
    def get_2hop_traversal(start_id: int) -> str:
        return f"MATCH (u:User {{id: {start_id}}})-[:FOLLOWS*2]->(m:User) RETURN DISTINCT m.id AS target_id, m.username AS username LIMIT 50"

    @staticmethod
    def get_3hop_traversal(start_id: int) -> str:
        return f"MATCH (u:User {{id: {start_id}}})-[:FOLLOWS*3]->(m:User) RETURN DISTINCT m.id AS target_id LIMIT 100"

    @staticmethod
    def get_point_lookup(user_id: int) -> str:
        return f"MATCH (u:User {{id: {user_id}}}) RETURN u.username, u.age, u.category, u.created_at"

    @staticmethod
    def get_indexed_lookup(category: str) -> str:
        return f"MATCH (u:User {{category: '{category}'}}) WHERE u.age > 30 RETURN u.id, u.username, u.age LIMIT 50"

    @staticmethod
    def get_aggregation_groupby() -> str:
        return """
        MATCH (u:User)-[r:FOLLOWS]->(m:User)
        RETURN u.category AS category, count(r) AS rel_count, avg(r.weight) AS avg_weight
        ORDER BY rel_count DESC
        """

    @staticmethod
    def get_write_transaction(src_id: int, dst_id: int, weight: float) -> str:
        return f"""
        MATCH (src:User {{id: {src_id}}}), (dst:User {{id: {dst_id}}})
        CREATE (src)-[:FOLLOWS {{weight: {weight}, interactions: 1}}]->(dst)
        """
