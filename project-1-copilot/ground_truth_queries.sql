-- Ground-truth queries for validating Claude's generated SQL
-- 1. Opportunities by deal stage
SELECT deal_stage, COUNT(*) AS count
FROM sales_pipeline
GROUP BY deal_stage;

-- 2. Total value of all won deals
SELECT SUM(close_value) AS total_won_value
FROM sales_pipeline
WHERE deal_stage = 'Won';

-- 3. Top 5 sales agents by total won value
SELECT sales_agent, SUM(close_value) AS total_value
FROM sales_pipeline
WHERE deal_stage = 'Won'
GROUP BY sales_agent
ORDER BY total_value DESC
LIMIT 5;

-- 4. Won/lost counts by regional office
SELECT st.regional_office,
       SUM(CASE WHEN sp.deal_stage = 'Won' THEN 1 ELSE 0 END) AS won,
       SUM(CASE WHEN sp.deal_stage = 'Lost' THEN 1 ELSE 0 END) AS lost
FROM sales_pipeline sp
JOIN sales_teams st ON sp.sales_agent = st.sales_agent
WHERE sp.deal_stage IN ('Won', 'Lost')
GROUP BY st.regional_office;