// with thanks to Micheal Hunter (https://gist.github.com/jexp)
// drop constraint chemical_nsc;
// drop constraint cell_line_name;
// drop constraint disease_name;
// drop constraint experiment_id;

return datetime();


LOAD CSV  WITH HEADERS FROM 'file:///GI50.csv' AS row 
RETURN count(*), count(distinct row.EXPID);

LOAD CSV  WITH HEADERS FROM 'file:///GI50.csv' AS row 
WITH distinct row.EXPID as experiment_id, row.NSC as nsc, row.CELL_NAME as cellName
RETURN count(*);

// fastest
:auto USING PERIODIC COMMIT 100000
LOAD CSV  WITH HEADERS FROM 'file:///GI50.csv' AS row 
WITH distinct row.CELL_NAME as cellName
CREATE (cell:CellLine {name: cellName});

:auto USING PERIODIC COMMIT 100000
LOAD CSV  WITH HEADERS FROM 'file:///GI50.csv' AS row 
WITH distinct row.PANEL_NAME as panelName
CREATE (dis:Disease {name: panelName});

:auto USING PERIODIC COMMIT 100000
LOAD CSV  WITH HEADERS FROM 'file:///GI50.csv' AS row 
WITH distinct toInteger(row.NSC) as nsc
CREATE (chem:Chemical {name: nsc});

:auto USING PERIODIC COMMIT 100000
LOAD CSV  WITH HEADERS FROM 'file:///GI50.csv' AS row 
WITH distinct row.EXPID as experimentId
CREATE (exp:Experiment {name: experimentId});

CREATE (r:Researcher {name: "NCI60"});
CREATE (m:MeasurementType {name: "GI50"});

CREATE constraint chemical_name if not exists for (c:Chemical) require c.name is unique;
CREATE constraint cell_line_name if not exists for (cl:CellLine) require cl.name is unique;
CREATE constraint disease_name if not exists for (d:Disease) require d.name is unique;
CREATE constraint experiment_name if not exists for (e:Experiment) require e.name is unique;
CREATE constraint researcher_name if not exists for (r:Researcher) require r.name is unique;
CREATE constraint measurement_name if not exists for (m:MeasurementType) require m.name is unique;

:auto USING PERIODIC COMMIT 100000
LOAD CSV  WITH HEADERS FROM 'file:///GI50.csv' AS row 
WITH distinct row.CELL_NAME as cellName, row.PANEL_NAME as panelName
MATCH (cell:CellLine {name: cellName})
MATCH (dis:Disease {name: panelName})
CREATE (cell)-[:CELL_LINE_OF]->(dis);


:auto USING PERIODIC COMMIT 100000
LOAD CSV  WITH HEADERS FROM 'file:///GI50.csv' AS row 
MATCH (chem:Chemical {name: toInteger(row.NSC)})
MATCH (cell:CellLine {name: row.CELL_NAME})
MATCH (exp:Experiment {name: row.EXPID})
MATCH (researcher:Researcher {name: "NCI60"})
MATCH (measurementType:MeasurementType {name: "GI50"})
CREATE (cond:Condition)<-[:PART_OF]-(exp)
CREATE (chem)<-[:USES]-(cond)
CREATE (cell)<-[:USES]-(cond)
CREATE (researcher)<-[:DONE_BY]-(cond)
CREATE (measurementType)<-[:MEASURES {concentration: row.AVERAGE, unit: row.CONCENTRATION_UNIT, count: row.COUNT}]-(cond);

return datetime()