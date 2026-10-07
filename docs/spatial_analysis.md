PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> notepad .\\docs\\spatial\_analysis.md

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> # Phase 3 - Spatial Analytics

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> ## 1. Objective

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> This phase analyzes the spatial distribution of crime, population, and economic activity across urban AGEBs in Mexico City.

This : El término 'This' no se reconoce como nombre de un cmdlet, función, archivo de script o

programa ejecutable. Compruebe si escribió correctamente el nombre o, si incluyó una ruta de

acceso, compruebe que dicha ruta es correcta e inténtelo de nuevo.

En línea: 1 Carácter: 1

\+ This phase analyzes the spatial distribution of crime, population, an ...

\+ \~\~\~\~

&#x20;   + CategoryInfo          : ObjectNotFound: (This:String) \[], CommandNotFoundException

&#x20;   + FullyQualifiedErrorId : CommandNotFoundException



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> The analysis uses the indicators already integrated into the PostgreSQL/PostGIS data warehouse. The main analytical source is `dw.vw\_kpi\_ageb`, joined with the geometries stored in `dw.dim\_geografia`.

The : El término 'The' no se reconoce como nombre de un cmdlet, función, archivo de script o

programa ejecutable. Compruebe si escribió correctamente el nombre o, si incluyó una ruta de

acceso, compruebe que dicha ruta es correcta e inténtelo de nuevo.

En línea: 1 Carácter: 1

\+ The analysis uses the indicators already integrated into the PostgreS ...

\+ \~\~\~

&#x20;   + CategoryInfo          : ObjectNotFound: (The:String) \[], CommandNotFoundException

&#x20;   + FullyQualifiedErrorId : CommandNotFoundException



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> The analysis includes:

The : El término 'The' no se reconoce como nombre de un cmdlet, función, archivo de script o

programa ejecutable. Compruebe si escribió correctamente el nombre o, si incluyó una ruta de

acceso, compruebe que dicha ruta es correcta e inténtelo de nuevo.

En línea: 1 Carácter: 1

\+ The analysis includes:

\+ \~\~\~

&#x20;   + CategoryInfo          : ObjectNotFound: (The:String) \[], CommandNotFoundException

&#x20;   + FullyQualifiedErrorId : CommandNotFoundException



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> - Three Spearman correlations.

En línea: 1 Carácter: 2

\+ - Three Spearman correlations.

\+  \~

Falta una expresión después del operador unario '-'.

En línea: 1 Carácter: 3

\+ - Three Spearman correlations.

\+   \~\~\~\~\~

Token 'Three' inesperado en la expresión o la instrucción.

&#x20;   + CategoryInfo          : ParserError: (:) \[], ParentContainsErrorRecordException

&#x20;   + FullyQualifiedErrorId : MissingExpressionAfterOperator



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> - Global Moran's I for two indicators.

>> - Local Moran's I (LISA).

En línea: 1 Carácter: 2

\+ - Global Moran's I for two indicators.

\+  \~

Falta una expresión después del operador unario '-'.

En línea: 1 Carácter: 3

\+ - Global Moran's I for two indicators.

\+   \~\~\~\~\~\~

Token 'Global' inesperado en la expresión o la instrucción.

&#x20;   + CategoryInfo          : ParserError: (:) \[], ParentContainsErrorRecordException

&#x20;   + FullyQualifiedErrorId : MissingExpressionAfterOperator



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> - Bivariate Moran's I.

>> - Descriptive thematic maps.

>>

>> The complete reproducible analysis is implemented in:

>>

>> `src/analysis/spatial\_analysis.py`

>>

>> ---

>>

>> ## 2. Spatial neighborhood rule

>>

>> The spatial weights use first-order Queen contiguity.

>>

>> Under Queen contiguity, two AGEBs are considered neighbors when their polygons share either a boundary or a vertex.

>>

>> The weights are row-standardized before calculating Moran statistics.

>>

>> The previous neighborhood analysis identified one Queen island in the complete set of 2,431 urban AGEBs. The selected strategy is to exclude islands from Moran and LISA because a spatial lag cannot be defined for an observation without neighbors.

>>

>> The neighborhood rule is documented independently in:

>>

>> `notebooks/02\_vecindad\_espacial.ipynb`

>>

>> Queen contiguity was selected because it represents direct geographic adjacency and does not require choosing an arbitrary distance or number of neighbors.

>>

>> The results of spatial statistics depend on the selected neighborhood definition. Therefore, the detected spatial association should be interpreted specifically under this Queen contiguity structure.

>>

>> ---

>>

>> ## 3. Analytical sample and missing values

>>

>> The data warehouse contains 2,431 urban AGEBs.

>>

>> Seventeen AGEBs have total population equal to zero. For these units, population-based indicators such as `crime\_rate\_per\_1000` cannot be calculated correctly and remain `NULL`.

>>

>> These missing values are not converted to zero because a missing rate is not equivalent to the absence of crime.

>>

>> For the spatial analysis, observations without the required indicators are excluded before constructing the final spatial weights matrix.

>>

>> After removing the 17 AGEBs with unavailable required KPIs, one Queen island remains:

>>

>> `090090015012A`

>>

>> This island is also excluded from Moran and LISA.

>>

>> Therefore:

>>

>> - Total AGEBs in the warehouse: 2,431

>> - AGEBs excluded because of unavailable KPI values: 17

>> - Queen islands excluded: 1

>> - Final AGEBs used for Moran/LISA: 2,413

>> - Average Queen neighbors in the analytical sample: 5.87

>> - Connected components: 5

>>

>> ---

>>

>> ## 4. Spearman correlations

>>

>> Spearman's rank correlation was selected because the urban indicators are not assumed to follow a normal distribution and can contain highly asymmetric values.

En línea: 1 Carácter: 2

\+ - Bivariate Moran's I.

\+  \~

Falta una expresión después del operador unario '-'.

En línea: 1 Carácter: 3

\+ - Bivariate Moran's I.

\+   \~\~\~\~\~\~\~\~\~

Token 'Bivariate' inesperado en la expresión o la instrucción.

&#x20;   + CategoryInfo          : ParserError: (:) \[], ParentContainsErrorRecordException

&#x20;   + FullyQualifiedErrorId : MissingExpressionAfterOperator



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> Three relationships were evaluated.

Three : El término 'Three' no se reconoce como nombre de un cmdlet, función, archivo de script o

programa ejecutable. Compruebe si escribió correctamente el nombre o, si incluyó una ruta de

acceso, compruebe que dicha ruta es correcta e inténtelo de nuevo.

En línea: 1 Carácter: 1

\+ Three relationships were evaluated.

\+ \~\~\~\~\~

&#x20;   + CategoryInfo          : ObjectNotFound: (Three:String) \[], CommandNotFoundException

&#x20;   + FullyQualifiedErrorId : CommandNotFoundException



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> | Relationship | Spearman rho | p-value | n |

>> |---|---:|---:|---:|

>> | Crime rate vs. business density | 0.2431 | 8.51e-34 | 2,414 |

>> | Crime rate vs. population density | -0.4002 | 1.57e-93 | 2,414 |

>> | Business density vs. population density | 0.4147 | 1.19e-101 | 2,431 |

>>

En línea: 1 Carácter: 1

\+ | Relationship | Spearman rho | p-value | n |

\+ \~

No se permiten elementos de canalización vacíos.

En línea: 1 Carácter: 46

\+ | Relationship | Spearman rho | p-value | n |

\+                                              \~

No se permiten elementos de canalización vacíos.

En línea: 2 Carácter: 5

\+ |---|---:|---:|---:|

\+     \~

Falta una expresión después del operador unario '-'.

En línea: 2 Carácter: 2

\+ |---|---:|---:|---:|

\+  \~\~\~

Las expresiones solo se permiten como primer elemento de las canalizaciones.

En línea: 2 Carácter: 9

\+ |---|---:|---:|---:|

\+         \~

Falta una expresión después del operador unario '-'.

En línea: 2 Carácter: 6

\+ |---|---:|---:|---:|

\+      \~\~\~

Las expresiones solo se permiten como primer elemento de las canalizaciones.

En línea: 2 Carácter: 9

\+ |---|---:|---:|---:|

\+         \~

Token ':' inesperado en la expresión o la instrucción.

En línea: 2 Carácter: 14

\+ |---|---:|---:|---:|

\+              \~

Falta una expresión después del operador unario '-'.

En línea: 2 Carácter: 11

\+ |---|---:|---:|---:|

\+           \~\~\~

Las expresiones solo se permiten como primer elemento de las canalizaciones.

En línea: 2 Carácter: 14

\+ |---|---:|---:|---:|

\+              \~

Token ':' inesperado en la expresión o la instrucción.

No se notificaron todos los errores de análisis. Corrija los errores notificados e inténtelo de

nuevo.

&#x20;   + CategoryInfo          : ParserError: (:) \[], ParentContainsErrorRecordException

&#x20;   + FullyQualifiedErrorId : EmptyPipeElement



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> ### Interpretation

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> Crime rate and business density have a positive but relatively weak association (`rho = 0.2431`). AGEBs with greater concentrations of establishments therefore tend to show somewhat higher crime rates, although the relationship is not strong.

>>

En línea: 1 Carácter: 243

\+ ... somewhat higher crime rates, although the relationship is not strong.

\+                                                                          \~

Falta el paréntesis de cierre ')' en la expresión.

&#x20;   + CategoryInfo          : ParserError: (:) \[], ParentContainsErrorRecordException

&#x20;   + FullyQualifiedErrorId : MissingEndParenthesisInExpression



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> Crime rate and population density show a moderate negative relationship (`rho = -0.4002`). In this dataset, more densely populated AGEBs tend to have lower crime rates per 1,000 residents.

>>

En línea: 1 Carácter: 189

\+ ... y populated AGEBs tend to have lower crime rates per 1,000 residents.

\+                                                                          \~

Falta el paréntesis de cierre ')' en la expresión.

&#x20;   + CategoryInfo          : ParserError: (:) \[], ParentContainsErrorRecordException

&#x20;   + FullyQualifiedErrorId : MissingEndParenthesisInExpression



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> Business density and population density show a moderate positive relationship (`rho = 0.4147`). Areas with greater population concentration also tend to contain a greater density of establishments.

>>

En línea: 1 Carácter: 198

\+ ... ncentration also tend to contain a greater density of establishments.

\+                                                                          \~

Falta el paréntesis de cierre ')' en la expresión.

&#x20;   + CategoryInfo          : ParserError: (:) \[], ParentContainsErrorRecordException

&#x20;   + FullyQualifiedErrorId : MissingEndParenthesisInExpression



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> All three relationships are statistically significant.

All : El término 'All' no se reconoce como nombre de un cmdlet, función, archivo de script o

programa ejecutable. Compruebe si escribió correctamente el nombre o, si incluyó una ruta de

acceso, compruebe que dicha ruta es correcta e inténtelo de nuevo.

En línea: 1 Carácter: 1

\+ All three relationships are statistically significant.

\+ \~\~\~

&#x20;   + CategoryInfo          : ObjectNotFound: (All:String) \[], CommandNotFoundException

&#x20;   + FullyQualifiedErrorId : CommandNotFoundException



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> These correlations describe association and do not demonstrate causal relationships.

These : El término 'These' no se reconoce como nombre de un cmdlet, función, archivo de script o

programa ejecutable. Compruebe si escribió correctamente el nombre o, si incluyó una ruta de

acceso, compruebe que dicha ruta es correcta e inténtelo de nuevo.

En línea: 1 Carácter: 1

\+ These correlations describe association and do not demonstrate causal ...

\+ \~\~\~\~\~

&#x20;   + CategoryInfo          : ObjectNotFound: (These:String) \[], CommandNotFoundException

&#x20;   + FullyQualifiedErrorId : CommandNotFoundException



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> The complete results are stored in:

The : El término 'The' no se reconoce como nombre de un cmdlet, función, archivo de script o

programa ejecutable. Compruebe si escribió correctamente el nombre o, si incluyó una ruta de

acceso, compruebe que dicha ruta es correcta e inténtelo de nuevo.

En línea: 1 Carácter: 1

\+ The complete results are stored in:

\+ \~\~\~

&#x20;   + CategoryInfo          : ObjectNotFound: (The:String) \[], CommandNotFoundException

&#x20;   + FullyQualifiedErrorId : CommandNotFoundException



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> `outputs/figures/correlaciones\_spearman.csv`

outputs/figures/correlaciones\_spearman.csv` : El término

'outputs/figures/correlaciones\_spearman.csv`' no se reconoce como nombre de un cmdlet, función,

archivo de script o programa ejecutable. Compruebe si escribió correctamente el nombre o, si

incluyó una ruta de acceso, compruebe que dicha ruta es correcta e inténtelo de nuevo.

En línea: 1 Carácter: 1

\+ `outputs/figures/correlaciones\_spearman.csv`

\+ \~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~

&#x20;   + CategoryInfo          : ObjectNotFound: (outputs/figures...s\_spearman.csv`:String) \[], Comman

&#x20;  dNotFoundException

&#x20;   + FullyQualifiedErrorId : CommandNotFoundException



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> ---

>>

En línea: 1 Carácter: 4

\+ ---

\+    \~

Falta una expresión después del operador unario '-'.

En línea: 1 Carácter: 3

\+ ---

\+   \~

El operador -- solamente funciona en variables o en propiedades.

&#x20;   + CategoryInfo          : ParserError: (:) \[], ParentContainsErrorRecordException

&#x20;   + FullyQualifiedErrorId : MissingExpressionAfterOperator



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> ## 5. Global Moran's I

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> Global Moran's I was calculated with 999 permutations and row-standardized Queen weights.

>>

>> Two indicators were evaluated:

>>

>> | Indicator | Moran's I | Expected I | Permutation p-value | n |

>> |---|---:|---:|---:|---:|

>> | Crime rate per 1,000 residents | 0.0138 | -0.0004 | 0.0450 | 2,413 |

>> | Business density | 0.4710 | -0.0004 | 0.0010 | 2,413 |

>>

En línea: 5 Carácter: 65

\+ | Indicator | Moran's I | Expected I | Permutation p-value | n |

\+                                                                 \~

No se permiten elementos de canalización vacíos.

En línea: 6 Carácter: 5

\+ |---|---:|---:|---:|---:|

\+     \~

Falta una expresión después del operador unario '-'.

En línea: 6 Carácter: 2

\+ |---|---:|---:|---:|---:|

\+  \~\~\~

Las expresiones solo se permiten como primer elemento de las canalizaciones.

En línea: 6 Carácter: 9

\+ |---|---:|---:|---:|---:|

\+         \~

Falta una expresión después del operador unario '-'.

En línea: 6 Carácter: 6

\+ |---|---:|---:|---:|---:|

\+      \~\~\~

Las expresiones solo se permiten como primer elemento de las canalizaciones.

En línea: 6 Carácter: 9

\+ |---|---:|---:|---:|---:|

\+         \~

Token ':' inesperado en la expresión o la instrucción.

En línea: 6 Carácter: 14

\+ |---|---:|---:|---:|---:|

\+              \~

Falta una expresión después del operador unario '-'.

En línea: 6 Carácter: 11

\+ |---|---:|---:|---:|---:|

\+           \~\~\~

Las expresiones solo se permiten como primer elemento de las canalizaciones.

En línea: 6 Carácter: 14

\+ |---|---:|---:|---:|---:|

\+              \~

Token ':' inesperado en la expresión o la instrucción.

En línea: 6 Carácter: 19

\+ |---|---:|---:|---:|---:|

\+                   \~

Falta una expresión después del operador unario '-'.

No se notificaron todos los errores de análisis. Corrija los errores notificados e inténtelo de

nuevo.

&#x20;   + CategoryInfo          : ParserError: (:) \[], ParentContainsErrorRecordException

&#x20;   + FullyQualifiedErrorId : EmptyPipeElement



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> ### Crime rate

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> The crime rate has a small positive Moran's I (`I = 0.0138`).

>>

>> The permutation p-value is `0.045`, which indicates statistically significant positive spatial autocorrelation at the 5% significance level. However, the magnitude of Moran's I is very small.

The : El término 'The' no se reconoce como nombre de un cmdlet, función, archivo de script o

programa ejecutable. Compruebe si escribió correctamente el nombre o, si incluyó una ruta de

acceso, compruebe que dicha ruta es correcta e inténtelo de nuevo.

En línea: 1 Carácter: 1

\+ The crime rate has a small positive Moran's I (`I = 0.0138`).

\+ \~\~\~

&#x20;   + CategoryInfo          : ObjectNotFound: (The:String) \[], CommandNotFoundException

&#x20;   + FullyQualifiedErrorId : CommandNotFoundException



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> Therefore, the evidence suggests that crime rates are not randomly distributed in space, but the global spatial clustering is weak.

En línea: 1 Carácter: 10

\+ Therefore, the evidence suggests that crime rates are not randomly di ...

\+          \~

Falta un argumento en la lista de parámetros.

&#x20;   + CategoryInfo          : ParserError: (:) \[], ParentContainsErrorRecordException

&#x20;   + FullyQualifiedErrorId : MissingArgument



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> ### Business density

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> Business density has a substantially larger positive Moran's I (`I = 0.4710`) with a permutation p-value of `0.001`.

>>

>> This indicates clear positive spatial autocorrelation. AGEBs with high business density tend to be located near other AGEBs with high business density, while low-density areas tend to be near other low-density areas.

>>

>> The results are stored in:

>>

>> `outputs/figures/moran\_global.csv`

>>

>> ---

>>

>> ## 6. Local Moran's I (LISA)

LISA : El término 'LISA' no se reconoce como nombre de un cmdlet, función, archivo de script o

programa ejecutable. Compruebe si escribió correctamente el nombre o, si incluyó una ruta de

acceso, compruebe que dicha ruta es correcta e inténtelo de nuevo.

En línea: 11 Carácter: 24

\+ ## 6. Local Moran's I (LISA)

\+                        \~\~\~\~

&#x20;   + CategoryInfo          : ObjectNotFound: (LISA:String) \[], CommandNotFoundException

&#x20;   + FullyQualifiedErrorId : CommandNotFoundException



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> Local Moran's I was calculated for `crime\_rate\_per\_1000` using 999 permutations.

>>

>> Only observations with a permutation p-value below `0.05` are classified as significant spatial clusters or spatial outliers.

>>

>> The LISA classification produced:

>>

>> | Cluster | Number of AGEBs |

>> |---|---:|

>> | High-High (HH) | 19 |

>> | Low-Low (LL) | 372 |

>> | Low-High (LH) | 98 |

>> | High-Low (HL) | 4 |

>> | Not significant (NS) | 1,920 |

>>

>> ### Interpretation

>>

>> High-High (HH) areas represent AGEBs with relatively high crime rates surrounded by neighbors that also have relatively high crime rates.

>>

>> Low-Low (LL) areas represent AGEBs with relatively low crime rates surrounded by other low-rate AGEBs.

>>

>> Low-High (LH) and High-Low (HL) observations are spatial outliers. Their value differs from the general pattern of their neighboring AGEBs.

>>

>> Most AGEBs are not locally significant, which is consistent with the weak magnitude observed in the Global Moran's I for crime rate.

Local : El término 'Local' no se reconoce como nombre de un cmdlet, función, archivo de script o

programa ejecutable. Compruebe si escribió correctamente el nombre o, si incluyó una ruta de

acceso, compruebe que dicha ruta es correcta e inténtelo de nuevo.

En línea: 1 Carácter: 1

\+ Local Moran's I was calculated for `crime\_rate\_per\_1000` using 999 pe ...

\+ \~\~\~\~\~

&#x20;   + CategoryInfo          : ObjectNotFound: (Local:String) \[], CommandNotFoundException

&#x20;   + FullyQualifiedErrorId : CommandNotFoundException



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> The LISA results are available in:

The : El término 'The' no se reconoce como nombre de un cmdlet, función, archivo de script o

programa ejecutable. Compruebe si escribió correctamente el nombre o, si incluyó una ruta de

acceso, compruebe que dicha ruta es correcta e inténtelo de nuevo.

En línea: 1 Carácter: 1

\+ The LISA results are available in:

\+ \~\~\~

&#x20;   + CategoryInfo          : ObjectNotFound: (The:String) \[], CommandNotFoundException

&#x20;   + FullyQualifiedErrorId : CommandNotFoundException



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> `outputs/figures/lisa\_crime\_rate.csv`

outputs/figures/lisa\_crime\_rate.csv` : El término 'outputs/figures/lisa\_crime\_rate.csv`' no se

reconoce como nombre de un cmdlet, función, archivo de script o programa ejecutable. Compruebe si

escribió correctamente el nombre o, si incluyó una ruta de acceso, compruebe que dicha ruta es

correcta e inténtelo de nuevo.

En línea: 1 Carácter: 1

\+ `outputs/figures/lisa\_crime\_rate.csv`

\+ \~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~

&#x20;   + CategoryInfo          : ObjectNotFound: (outputs/figures/lisa\_crime\_rate.csv`:String) \[], Com

&#x20;  mandNotFoundException

&#x20;   + FullyQualifiedErrorId : CommandNotFoundException



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> The corresponding map is:

The : El término 'The' no se reconoce como nombre de un cmdlet, función, archivo de script o

programa ejecutable. Compruebe si escribió correctamente el nombre o, si incluyó una ruta de

acceso, compruebe que dicha ruta es correcta e inténtelo de nuevo.

En línea: 1 Carácter: 1

\+ The corresponding map is:

\+ \~\~\~

&#x20;   + CategoryInfo          : ObjectNotFound: (The:String) \[], CommandNotFoundException

&#x20;   + FullyQualifiedErrorId : CommandNotFoundException



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> `outputs/maps/lisa\_crime\_rate.png`

outputs/maps/lisa\_crime\_rate.png` : El término 'outputs/maps/lisa\_crime\_rate.png`' no se reconoce

como nombre de un cmdlet, función, archivo de script o programa ejecutable. Compruebe si escribió

correctamente el nombre o, si incluyó una ruta de acceso, compruebe que dicha ruta es correcta e

inténtelo de nuevo.

En línea: 1 Carácter: 1

\+ `outputs/maps/lisa\_crime\_rate.png`

\+ \~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~\~

&#x20;   + CategoryInfo          : ObjectNotFound: (outputs/maps/lisa\_crime\_rate.png`:String) \[], Comman

&#x20;  dNotFoundException

&#x20;   + FullyQualifiedErrorId : CommandNotFoundException



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> ---

>>

En línea: 1 Carácter: 4

\+ ---

\+    \~

Falta una expresión después del operador unario '-'.

En línea: 1 Carácter: 3

\+ ---

\+   \~

El operador -- solamente funciona en variables o en propiedades.

&#x20;   + CategoryInfo          : ParserError: (:) \[], ParentContainsErrorRecordException

&#x20;   + FullyQualifiedErrorId : MissingExpressionAfterOperator



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> ## 7. Bivariate spatial association

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence>

PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> A Bivariate Moran's I was calculated between:

>>

>> - `crime\_rate\_per\_1000` for each AGEB, and

>> - the spatial lag of `business\_density` in neighboring AGEBs.

>>

>> The result was:

>>

>> | Relationship | Bivariate Moran's I | Permutation p-value | n |

>> |---|---:|---:|---:|

>> | Crime rate vs. neighboring business density | 0.0218 | 0.0140 | 2,413 |

>>

En línea: 8 Carácter: 65

\+ | Relationship | Bivariate Moran's I | Permutation p-value | n |

\+                                                                 \~

No se permiten elementos de canalización vacíos.

En línea: 9 Carácter: 5

\+ |---|---:|---:|---:|

\+     \~

Falta una expresión después del operador unario '-'.

En línea: 9 Carácter: 2

\+ |---|---:|---:|---:|

\+  \~\~\~

Las expresiones solo se permiten como primer elemento de las canalizaciones.

En línea: 9 Carácter: 9

\+ |---|---:|---:|---:|

\+         \~

Falta una expresión después del operador unario '-'.

En línea: 9 Carácter: 6

\+ |---|---:|---:|---:|

\+      \~\~\~

Las expresiones solo se permiten como primer elemento de las canalizaciones.

En línea: 9 Carácter: 9

\+ |---|---:|---:|---:|

\+         \~

Token ':' inesperado en la expresión o la instrucción.

En línea: 9 Carácter: 14

\+ |---|---:|---:|---:|

\+              \~

Falta una expresión después del operador unario '-'.

En línea: 9 Carácter: 11

\+ |---|---:|---:|---:|

\+           \~\~\~

Las expresiones solo se permiten como primer elemento de las canalizaciones.

En línea: 9 Carácter: 14

\+ |---|---:|---:|---:|

\+              \~

Token ':' inesperado en la expresión o la instrucción.

En línea: 9 Carácter: 19

\+ |---|---:|---:|---:|

\+                   \~

Falta una expresión después del operador unario '-'.

No se notificaron todos los errores de análisis. Corrija los errores notificados e inténtelo de

nuevo.

&#x20;   + CategoryInfo          : ParserError: (:) \[], ParentContainsErrorRecordException

&#x20;   + FullyQualifiedErrorId : EmptyPipeElement



PS C:\\Users\\usuario\\Documents\\cdmx-urban-intelligence> The positive value indicates a weak positive spatial relationship between an AGEB's crime rate and the business density of its neighboring AGEBs.

>>

>> The permutation p-value (`0.014`) indicates that the observed spatial association is statistically significant at the 5% level.

>>

>> However, the magnitude of the statistic is small. Therefore, neighboring business density is spatially associated with crime rate, but the relationship should not be described as strong.

>>

>> The result is stored in:

>>

>> `outputs/figures/moran\_bivariado.csv`

>>

>> ---

>>

>> ## 8. Maps

>>

>> The analysis generates the following descriptive maps:

>>

>> - `outputs/maps/crime\_rate\_per\_1000.png`

>> - `outputs/maps/business\_density.png`

>> - `outputs/maps/population\_density.png`

>> - `outputs/maps/lisa\_crime\_rate.png`

>>

>> These maps provide a geographic comparison of crime, population, business activity, and statistically significant local crime clusters.

>>

>> ---

>>

>> ## 9. Reproducibility

>>

>> The complete analysis can be executed from the application container with:

>>

>> ```bash

>> docker compose exec app python -m src.analysis.spatial\_analysis









