"""Idempotent curriculum seed. Run with: python -m app.data.seed"""
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models import LearningModule, LearningProject, LearningResource, LearningTask, LearningTopic, LearningTrack, ProjectMilestone, Skill, TaskPrerequisite

SKILLS = [
    ("python", "Python for Data Science"), ("sql", "SQL"), ("probability", "Probability"),
    ("statistics", "Statistics"), ("linear-algebra", "Linear algebra"), ("eda", "Exploratory analysis"),
    ("machine-learning", "Machine learning"), ("feature-engineering", "Feature engineering"),
    ("model-evaluation", "Model evaluation"), ("experimentation", "Experimentation"),
    ("time-series", "Time-series analysis"), ("communication", "Communication"),
]

# Track, module, topic, task title, minutes, difficulty, type, practical exercise, completion evidence, skill slugs
TASKS = [
 ("Exploratory Data Analysis","Data foundations","Array reasoning","Vectorized NumPy transformations",60,2,"practice","Implement normalization, winsorization, and grouped calculations without Python loops; benchmark against a loop baseline.","A tested notebook with timing comparison and a short explanation of broadcasting.",["python","eda"]),
 ("Exploratory Data Analysis","Data foundations","Tabular workflows","Audit an unfamiliar dataset",90,2,"practice","Build a reusable Pandas audit reporting schema, types, cardinality, missingness, duplicates, and suspicious ranges.","An audit table plus five evidence-backed data quality observations.",["python","eda"]),
 ("Exploratory Data Analysis","Data foundations","Tabular workflows","Design reliable cleaning rules",120,3,"practice","Define deterministic rules for types, duplicates, category normalization, impossible values, and provenance columns.","A reproducible cleaning function with assertions and before/after quality metrics.",["python","eda"]),
 ("Exploratory Data Analysis","Data quality","Missing data","Diagnose missingness mechanisms",90,3,"theory","Compare missingness across target, cohorts, and observed covariates; reason about MCAR, MAR, and MNAR.","A missingness matrix, two statistical comparisons, and a documented mechanism hypothesis.",["statistics","eda"]),
 ("Exploratory Data Analysis","Data quality","Missing data","Evaluate imputation strategies",120,3,"practice","Compare deletion, simple imputation, and model-based imputation using leakage-safe validation.","Validation results, uncertainty notes, and a justified production choice.",["statistics","eda","model-evaluation"]),
 ("Exploratory Data Analysis","Data quality","Outliers","Distinguish anomalies from rare valid cases",75,3,"practice","Use robust z-scores, IQR rules, and domain constraints; inspect the cases each method flags.","A labelled anomaly table and treatment decisions with domain rationale.",["statistics","eda"]),
 ("Exploratory Data Analysis","Visual investigation","Distributions","Read distributions beyond averages",60,2,"practice","Compare ECDFs, histograms, KDEs, and quantile plots for skewed variables.","Four plots with interpretations of skew, tails, modality, and scale.",["eda","statistics"]),
 ("Exploratory Data Analysis","Visual investigation","Relationships","Investigate correlation responsibly",90,3,"practice","Compare Pearson, Spearman, partial correlations, and non-linear plots on mixed relationships.","A relationship report identifying confounding, non-linearity, and fragile conclusions.",["eda","statistics"]),
 ("Exploratory Data Analysis","Visual investigation","Multivariate patterns","Reveal structure with coordinated views",120,3,"practice","Use faceting, color, small multiples, and dimensionality reduction to investigate interacting variables.","A concise visual narrative with three findings and one falsified initial assumption.",["eda","communication","linear-algebra"]),
 ("Exploratory Data Analysis","Visual investigation","Pattern discovery","Turn EDA findings into testable questions",60,3,"reflection","Convert exploratory observations into explicit hypotheses and proposed validation procedures.","At least five hypotheses, each separating observation, mechanism, and validation plan.",["eda","communication"]),

 ("Statistics & Experimentation","Probability foundations","Random variables","Simulate probability concepts",75,2,"practice","Simulate conditional probability, Bayes updates, the law of large numbers, and selection bias.","A reproducible simulation notebook whose empirical results match analytical expectations.",["probability","python"]),
 ("Statistics & Experimentation","Probability foundations","Distributions","Choose distributions from data-generating processes",90,3,"theory","Map Bernoulli, binomial, Poisson, normal, lognormal, and beta distributions to realistic processes.","A comparison table with assumptions, parameters, failure cases, and simulated examples.",["probability","statistics"]),
 ("Statistics & Experimentation","Inference","Sampling","Measure sampling variability",60,2,"practice","Draw repeated samples from a known population and examine estimator bias and variance.","Sampling distributions for mean and median plus a written bias-variance comparison.",["statistics","probability"]),
 ("Statistics & Experimentation","Inference","Confidence intervals","Construct and interpret confidence intervals",90,3,"practice","Compute analytic and bootstrap intervals for means, proportions, and a skewed metric.","Correct coverage interpretation and a simulation checking empirical coverage.",["statistics","experimentation"]),
 ("Statistics & Experimentation","Inference","Hypothesis testing","Reason about tests, not just p-values",90,3,"practice","State estimands and assumptions, run appropriate tests, report effect sizes, and examine sensitivity.","A decision memo distinguishing statistical from practical significance.",["statistics","experimentation","communication"]),
 ("Statistics & Experimentation","Inference","Power","Plan sample size and power",75,3,"practice","Create power curves across effect sizes, variance, allocation ratios, and significance thresholds.","A sample-size recommendation with minimum detectable effect and assumptions.",["statistics","experimentation"]),
 ("Statistics & Experimentation","Inference","Bootstrap","Use resampling for difficult estimators",90,3,"practice","Bootstrap a median difference and a model performance metric; compare percentile and BCa concepts.","Stable interval estimates plus a discussion of resampling limitations.",["statistics","model-evaluation"]),
 ("Statistics & Experimentation","Experiments","A/B testing","Analyze an online experiment end to end",150,4,"project","Check randomization, define the estimand, estimate treatment effect, quantify uncertainty, and check guardrails.","A reproducible analysis and decision-ready recommendation with caveats.",["experimentation","statistics","communication"]),
 ("Statistics & Experimentation","Experiments","Experimental design","Design an experiment before seeing results",90,4,"practice","Specify hypothesis, unit, exposure, metrics, variance reduction, power, stopping rule, and validity threats.","A preregistration-style experiment plan another analyst could execute.",["experimentation","statistics"]),
 ("Statistics & Experimentation","Experiments","Causal fundamentals","Draw a causal graph and identify an effect",120,4,"theory","Build a DAG for a realistic business question; identify confounders, mediators, colliders, and adjustment sets.","A DAG plus a defensible identification argument and sensitivity concerns.",["experimentation","statistics"]),

 ("Classical Machine Learning","Supervised foundations","Regression","Build and diagnose regression models",120,3,"practice","Fit linear and robust baselines; inspect residual structure, leverage, heteroscedasticity, and coefficient stability.","Cross-validated metrics and a residual diagnostic report tied to remedies.",["machine-learning","model-evaluation","statistics"]),
 ("Classical Machine Learning","Supervised foundations","Classification","Establish a classification baseline",120,3,"practice","Compare dummy, logistic, and tree baselines under class imbalance and asymmetric costs.","A leakage-safe pipeline, chosen threshold, and cost-aware evaluation.",["machine-learning","model-evaluation"]),
 ("Classical Machine Learning","Supervised foundations","Regularization","Understand regularization paths",90,3,"practice","Trace L1 and L2 coefficient paths under correlated predictors and varying sample sizes.","Plots and explanation of shrinkage, selection instability, and scaling requirements.",["machine-learning","linear-algebra"]),
 ("Classical Machine Learning","Tree ensembles","Decision trees","Explain tree decisions and overfitting",75,2,"practice","Vary depth and leaf constraints; visualize partitions and compare train-validation behavior.","A complexity curve and plain-language explanation of two predictions.",["machine-learning","model-evaluation"]),
 ("Classical Machine Learning","Tree ensembles","Random forests","Measure ensemble diversity",90,3,"practice","Inspect out-of-bag error, feature subsampling, tree correlation, and permutation importance.","A parameter sensitivity report and honest feature-importance caveats.",["machine-learning","model-evaluation"]),
 ("Classical Machine Learning","Tree ensembles","Gradient boosting","Tune boosting systematically",150,4,"practice","Tune learning rate, trees, depth, sampling, and early stopping within nested validation.","A search record, validation curve, final holdout result, and overfitting analysis.",["machine-learning","model-evaluation"]),
 ("Classical Machine Learning","Unsupervised learning","Clustering","Validate useful segments",120,3,"practice","Compare k-means, hierarchical, and density clustering after appropriate scaling.","Stability analysis, cluster profiles, and a statement of whether segments are actionable.",["machine-learning","eda"]),
 ("Classical Machine Learning","Unsupervised learning","Dimensionality reduction","Interpret PCA geometrically",90,3,"practice","Standardize data, inspect explained variance and loadings, reconstruct observations, and visualize scores.","A geometric explanation, scree plot, loading analysis, and reconstruction error.",["machine-learning","linear-algebra","eda"]),
 ("Classical Machine Learning","Reliable modeling","Feature engineering","Build leakage-safe features",120,4,"practice","Create temporal, aggregate, interaction, and encoding features entirely inside validation folds.","A pipeline plus an explicit leakage audit and feature ablation results.",["feature-engineering","machine-learning"]),
 ("Classical Machine Learning","Reliable modeling","Cross-validation","Choose validation that matches deployment",90,4,"theory","Compare random, stratified, grouped, and time-aware splits for three deployment scenarios.","Split diagrams and justified validation designs with leakage risks.",["model-evaluation","machine-learning"]),
 ("Classical Machine Learning","Reliable modeling","Interpretability","Explain models without overclaiming",120,4,"practice","Compare permutation importance, PDP/ALE, and SHAP on correlated features.","Global and local explanations with stability checks and causal disclaimers.",["model-evaluation","communication"]),
 ("Classical Machine Learning","Reliable modeling","Error analysis","Turn errors into model improvements",90,3,"practice","Slice errors by meaningful cohorts, inspect high-loss cases, and classify failure modes.","An error taxonomy, quantified slices, and prioritized follow-up experiments.",["model-evaluation","eda"]),
 ("Classical Machine Learning","Reliable modeling","Calibration","Calibrate probabilistic predictions",90,4,"practice","Compare reliability curves, Brier score, Platt scaling, and isotonic regression.","Out-of-fold calibration results and a threshold policy tied to decisions.",["model-evaluation","statistics"]),

 ("SQL & Data Engineering","Analytical SQL","Window functions","Answer cohort questions with windows",90,3,"practice","Write retention, rolling average, ranking, and sessionization queries over event data.","Four correct queries with edge-case fixtures and explained window frames.",["sql"]),
 ("SQL & Data Engineering","Analytical SQL","CTEs","Structure a maintainable analytical query",75,3,"practice","Refactor a nested business query into named CTE stages with tests at each grain.","A readable query, grain annotations, and reconciliation checks.",["sql","communication"]),
 ("SQL & Data Engineering","Analytical SQL","Query correctness","Prevent join and aggregation errors",90,3,"practice","Diagnose fan-out, null behavior, denominator drift, and slowly changing dimension issues.","A test suite of adversarial fixtures and corrected metrics.",["sql","statistics"]),
 ("SQL & Data Engineering","Data products","Transformation","Model an analytics-ready dataset",120,3,"project","Design facts, dimensions, keys, grains, and incremental transformations for a product funnel.","A schema diagram, transformation SQL, and metric reconciliation.",["sql","feature-engineering"]),
 ("SQL & Data Engineering","Data products","Pipelines","Build an idempotent data pipeline",150,4,"project","Ingest raw files, validate schema, transform records, and publish partitioned analytical output.","A rerunnable pipeline with logs, checkpoints, and failure recovery notes.",["python","sql"]),
 ("SQL & Data Engineering","Data products","Data quality","Define data contracts and checks",90,3,"practice","Specify freshness, uniqueness, validity, referential, and distribution checks for a model input table.","Executable checks with severity levels, owners, and response guidance.",["sql","model-evaluation"]),

 ("Research & Communication","Research practice","Scientific reading","Critically read an empirical paper",90,3,"reflection","Extract the question, estimand, data, assumptions, methods, results, limitations, and reproducibility gaps.","A one-page structured critique with three follow-up questions.",["communication","statistics"]),
 ("Research & Communication","Research practice","Methodology","Write a falsifiable analysis plan",75,3,"theory","Turn an ambiguous business problem into hypotheses, measures, design, analysis, and decision rules.","A preregistered plan separating confirmatory and exploratory work.",["communication","experimentation"]),
 ("Research & Communication","Research practice","Reproducibility","Create a reproducible experiment package",120,3,"project","Pin dependencies, set seeds, separate data/code/output, add configuration, and automate the main report.","A clean-environment run reproduces the key table and figure.",["python","communication"]),
 ("Research & Communication","Analytical communication","Reporting","Write an executive analytical memo",90,3,"practice","Condense a technical analysis into context, result, uncertainty, recommendation, and next action.","A two-page memo with traceable evidence and no unsupported causal language.",["communication"]),
 ("Research & Communication","Analytical communication","Data storytelling","Design a focused data narrative",90,3,"practice","Choose a decision, audience, sequence, and minimal set of visuals; remove decorative complexity.","A five-slide narrative tested against a clear audience takeaway.",["communication","eda"]),
 ("Research & Communication","Analytical communication","Portfolio","Publish a defensible case study",180,4,"project","Turn one analysis into a polished case study covering framing, data, method, findings, limits, and reproducibility.","A public-ready README, reproducible repository, and concise results presentation.",["communication","eda","model-evaluation"]),
]

RESOURCES = [
 ("An Introduction to Statistical Learning with Python","https://www.statlearning.com/","book","Machine learning",2,"Free, rigorous introduction pairing statistical ideas with Python labs."),
 ("StatQuest","https://statquest.org/video_index.html","video","Statistics",1,"Clear conceptual explanations of statistics and machine learning."),
 ("Kaggle Learn","https://www.kaggle.com/learn","course","Practice",1,"Short hands-on courses with executable exercises."),
 ("scikit-learn User Guide","https://scikit-learn.org/stable/user_guide.html","documentation","Machine learning",3,"Authoritative model, pipeline, evaluation, and inspection documentation."),
 ("SciPy Statistics","https://docs.scipy.org/doc/scipy/reference/stats.html","documentation","Statistics",3,"Reference for probability distributions and statistical tests."),
 ("statsmodels Documentation","https://www.statsmodels.org/stable/index.html","documentation","Statistics",3,"Statistical modeling, inference, diagnostics, and time series."),
 ("Mathematics for Machine Learning","https://mml-book.github.io/","book","Mathematics",3,"Free text covering linear algebra, calculus, probability, and ML foundations."),
 ("Causal Inference: The Mixtape","https://mixtape.scunning.com/","book","Causal inference",4,"Open textbook with practical causal inference designs."),
 ("Interpretable Machine Learning","https://christophm.github.io/interpretable-ml-book/","book","Interpretability",3,"Open guide to model-agnostic and model-specific interpretation."),
]

PROJECTS = [
 ("customer-churn","Customer Churn Prediction","Investigate churn drivers and build a calibrated, decision-aware classifier.","https://www.kaggle.com/datasets/blastchar/telco-customer-churn",["EDA","feature engineering","classification","interpretability"],[
  ("Data audit and problem framing","Define churn, prediction moment, business action, leakage boundaries, and data quality risks.","An audit notebook and one-page problem statement."),
  ("Exploratory analysis","Quantify churn across tenure, service, contract, and billing cohorts with uncertainty.","A focused EDA report with at least five validated findings."),
  ("Baseline and validation","Build dummy and logistic baselines with a deployment-aligned split.","Reproducible pipeline and justified primary metric."),
  ("Feature engineering and models","Compare leakage-safe features and tree ensembles using cross-validation.","Ablation table and honest model comparison."),
  ("Error analysis and explanation","Analyze cohort errors, calibration, thresholds, and stable explanations.","Error taxonomy, calibration plot, and action policy."),
  ("Portfolio publication","Document results, limitations, reproducibility, and business recommendations.","Public-ready repository and concise case study.")]),
 ("ab-testing","A/B Testing & Causal Analysis","Analyze a product experiment and communicate a decision under uncertainty.","https://www.kaggle.com/datasets/zhangluyuan/ab-testing",["inference","experimentation","causal analysis","communication"],[
  ("Experiment specification","Define unit, treatment, estimand, success metric, guardrails, and validity risks.","A preregistration-style analysis plan."),
  ("Integrity checks","Check sample ratio mismatch, duplication, exposure timing, and covariate balance.","A documented integrity report."),
  ("Effect estimation","Estimate absolute and relative effects with confidence intervals and sensitivity analyses.","Reproducible estimates with assumptions."),
  ("Heterogeneity and robustness","Explore pre-specified segments and robustness without p-hacking.","A clearly labeled exploratory analysis."),
  ("Decision memo","Translate evidence, uncertainty, costs, and risks into a recommendation.","A decision-ready two-page memo.")]),
 ("nlp-analytics","NLP Analytics & Pattern Discovery","Discover themes in text and test whether they predict meaningful outcomes.","https://www.kaggle.com/datasets/snap/amazon-fine-food-reviews",["text analysis","clustering","classification","embeddings"],[
  ("Corpus audit","Study sampling, text quality, labels, duplication, time, and leakage.","A corpus card and quality report."),
  ("Descriptive text analysis","Measure vocabulary, length, sentiment proxies, and temporal/category differences.","A reproducible descriptive report."),
  ("Topic discovery","Compare sparse and embedding representations for clustering or topic discovery.","Interpretable topic profiles and stability assessment."),
  ("Predictive baseline","Build a leakage-safe text classification baseline and evaluate cohort errors.","Cross-validated metrics and error slices."),
  ("Statistical comparison","Test selected differences with effect sizes and multiplicity awareness.","A compact inference table with caveats."),
  ("Publish findings","Present patterns, predictive limits, ethical concerns, and reproducibility.","A polished case study and repository.")]),
]


def seed() -> None:
    with SessionLocal() as db:
        if db.scalar(select(LearningTrack.id).limit(1)):
            print("Curriculum already seeded")
            return
        skills = {}
        for slug, name in SKILLS:
            item = Skill(slug=slug, name=name, description=f"Demonstrated ability in {name.lower()} through exercises, assessments, and project evidence.")
            db.add(item); db.flush(); skills[slug] = item
        track_order = list(dict.fromkeys(row[0] for row in TASKS)); tracks = {}
        for pos, title in enumerate(track_order):
            track = LearningTrack(slug=title.lower().replace(" & ", "-").replace(" ", "-"), title=title, description=f"A practical progression through {title.lower()} with evidence-based completion.", position=pos)
            db.add(track); db.flush(); tracks[title] = track
        modules, topics, previous_by_module = {}, {}, {}
        for pos, row in enumerate(TASKS):
            track_name, module_name, topic_name, title, minutes, difficulty, kind, exercise, criteria, tags = row
            mkey = (track_name, module_name)
            if mkey not in modules:
                module = LearningModule(track_id=tracks[track_name].id, title=module_name, description=f"Develop practical capability in {module_name.lower()}.", position=len([x for x in modules if x[0] == track_name]))
                db.add(module); db.flush(); modules[mkey] = module
            tkey = (*mkey, topic_name)
            if tkey not in topics:
                topic = LearningTopic(module_id=modules[mkey].id, title=topic_name, description=f"Concepts and applied work for {topic_name.lower()}.", position=len([x for x in topics if x[:2] == mkey]))
                db.add(topic); db.flush(); topics[tkey] = topic
            task = LearningTask(topic_id=topics[tkey].id, title=title, description=f"Study and apply {title.lower()} in a realistic analytical setting.", objectives=[f"Explain the key ideas behind {topic_name.lower()}", "Apply the method to real data", "Evaluate assumptions and limitations"], duration_minutes=minutes, difficulty=difficulty, task_type=kind, practical_exercise=exercise, completion_criteria=criteria, position=pos, priority=70 if kind in {"practice","project"} else 55)
            task.skills = [skills[x] for x in tags]; db.add(task); db.flush()
            if mkey in previous_by_module:
                db.add(TaskPrerequisite(task_id=task.id, prerequisite_id=previous_by_module[mkey]))
            previous_by_module[mkey] = task.id
        for title, url, kind, topic, difficulty, description in RESOURCES:
            db.add(LearningResource(title=title, url=url, resource_type=kind, topic=topic, difficulty=difficulty, description=description))
        for pos, (slug, title, description, dataset, tags, milestones) in enumerate(PROJECTS):
            project = LearningProject(slug=slug, title=title, description=description, dataset_url=dataset, skill_tags=tags, objectives=["Frame a defensible analytical question", "Produce reproducible evidence", "Communicate decisions and limitations"], position=pos)
            db.add(project); db.flush()
            for mpos, (mtitle, mdesc, criteria) in enumerate(milestones):
                db.add(ProjectMilestone(project_id=project.id, title=mtitle, description=mdesc, completion_criteria=criteria, position=mpos))
        db.commit(); print(f"Seeded {len(TASKS)} tasks, {len(RESOURCES)} resources, and {len(PROJECTS)} projects")


if __name__ == "__main__": seed()
