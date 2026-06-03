# Retail Data Warehouse — MySQL NDB Cluster

Un entrepôt de données retail unifiant trois systèmes sources (POS, ERP, E-commerce) dans un cluster MySQL NDB, avec pipeline ETL Python et couche analytique intégrée.

---

## Architecture

Trois systèmes sources alimentent un pipeline ETL Python (extraction → nettoyage → chargement), qui charge un cluster MySQL NDB composé d'un nœud de gestion, deux nœuds de données en réplication, et un nœud SQL exposé sur le port 3306. La couche analytique s'appuie sur des requêtes SQL, des procédures stockées, et Metabase pour la visualisation.

```
┌─────────────────────────────────────────────┐
│              SOURCE SYSTEMS                 │
│   ┌───────┐     ┌───────┐     ┌──────────┐  │
│   │  POS  │     │  ERP  │     │E-commerce│  │
│   └───┬───┘     └───┬───┘     └────┬─────┘  │
└───────┼─────────────┼──────────────┼────────┘
        └─────────────┴──────────────┘
                      │
          ┌───────────▼───────────┐
          │     ETL PIPELINE      │
          │  Python · Pandas      │
          │  Extract → Clean → Load│
          └───────────┬───────────┘
                      │
       ┌──────────────▼──────────────────┐
       │       MYSQL NDB CLUSTER         │
       │                                 │
       │  ┌──────────────────────────┐   │
       │  │     Management node      │   │
       │  │     Port :1186           │   │
       │  └────────────┬─────────────┘   │
       │               │                 │
       │      ┌────────┴────────┐        │
       │      ▼                 ▼        │
       │  ┌────────┐       ┌────────┐   │
       │  │  DN 1  │       │  DN 2  │   │
       │  └────────┘       └────────┘   │
       │           \       /             │
       │        ┌───▼─────▼───┐          │
       │        │  SQL node   │          │
       │        │  Port :3306 │          │
       │        └─────────────┘          │
       └─────────────────────────────────┘
                      │
       ┌──────────────▼──────────────────┐
       │        ANALYTICS LAYER          │
       │  7 SQL queries ·                │
       │  Metabase BI ·                  │
       └─────────────────────────────────┘
```

---

## Star Schema

**Grain :** une ligne par article vendu .

```
          dim_time
              │
dim_customers─┼─ fact_sales ─┬─ dim_products
              │               │
          dim_stores──────────┘
```





## Environnements

| Env  | Usage               | Port | Extra          |
|------|---------------------|------|----------------|
| DEV  | Développement local | 3306 | Adminer :8080  |
| TEST | CI / intégration    | 3307 | —              |
| PROD | Production          | 3306 | —              |
| DAC  | BI & analytics      | 3308 | Metabase :3000 |

```

```

---

## Analytiques disponibles

| # | Description |
|---|-------------|
| 1 | Revenue par store — net revenue, marge, panier moyen |
| 2 | Tendances mensuelles — croissance MoM, unités, remises |
| 3 | Top 10 produits — revenue, marge, taux de retour |
| 4 | Impact promotions — comparaison promu vs non-promu |
| 5 | Panier moyen / RFM — segmentation client, récence |
| 6 | Revenue par catégorie × canal — POS / ERP / E-commerce |
| 7 | Weekend vs semaine — comparaison de performance |
