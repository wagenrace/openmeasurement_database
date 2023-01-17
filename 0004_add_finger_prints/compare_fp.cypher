MATCH (c1:Compound {pubChemCompId: 69361793})

MATCH (c1)-[:HAS_FINGERPRINT]->(fp1:Fingerprint)
WITH count(fp1) as count_fp1, c1
    
MATCH (c1)-[:HAS_FINGERPRINT]->(fp:Fingerprint)<-[:HAS_FINGERPRINT]-(c2:Compound)
WITH DISTINCT c2, count(fp) as count_intersection, count_fp1
CALL{
    WITH c2, count_intersection, count_fp1
    
    CALL{
        WITH c2
        MATCH (c2)-[:HAS_FINGERPRINT]->(fp2:Fingerprint)
        RETURN count(fp2) as count_fp2
    }
    RETURN toFloat(count_intersection)/(count_fp1 + count_fp2 - count_intersection) as tanimoto
}
RETURN c2, tanimoto ORDER BY tanimoto limit 25