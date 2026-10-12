# ADR-0003: Procesamiento híbrido entre Google Earth Engine y Python local

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-09-29 |
| **Origen** | Fase 1, registrado retroactivamente |
| **Relacionado con** | RF-01 a RF-06, RNF-01, RNF-02, ADR-0004, ADR-0018 |

## Contexto

El conjunto de calibración incluye los incendios del Biobío entre 2020 y 2025,
cada uno con un par de imágenes Sentinel-2 pre y post incendio. Descargar las
escenas completas implica decenas de gigabytes, mientras que el equipo de
trabajo dispone de 16 GB de RAM y almacenamiento limitado.

Por otra parte, la umbralización multinivel de Otsu y la estimación de
densidad kernel no tienen funciones nativas equivalentes en Earth Engine a las
de `scikit-image` y `scipy`.

## Opciones consideradas

1. **Procesamiento íntegramente local** con `rasterio`.
   *Ventaja:* control total de cada paso. *Limitación:* requiere descargar y
   almacenar escenas completas.
2. **Procesamiento íntegramente en Google Earth Engine.**
   *Ventaja:* sin problemas de almacenamiento y con acceso directo al
   catálogo. *Limitación:* dificulta implementar Otsu multinivel y KDE, que
   son el núcleo metodológico del proyecto.
3. **Esquema híbrido.** Earth Engine compone las imágenes, enmascara nubes y
   calcula los índices; Python local ejecuta la umbralización y el análisis
   estadístico.
   *Ventaja:* combina el catálogo en la nube con el control local de la etapa
   metodológica. *Limitación:* introduce una frontera entre dos entornos.

## Decisión

Se adopta el esquema híbrido. Earth Engine realiza la composición de imágenes
libres de nubes, el enmascaramiento y el cálculo de índices, y exporta solo
los valores de píxel recortados y estratificados. La umbralización, la
consolidación estadística y la evaluación de exactitud se ejecutan localmente
en Python, con lectura por ventanas para respetar el límite de memoria
(RNF-01).

## Consecuencias

**Positivas**
- Se evita el cuello de botella de almacenamiento.
- La etapa donde reside el aporte metodológico permanece bajo control local.
- Earth Engine es la misma plataforma que CONAF emplea para calcular el dNBR,
  lo que facilita una eventual adopción institucional.

**Negativas**
- Las exportaciones desde Earth Engine son asíncronas y tienen límites de
  tamaño por solicitud, por lo que las áreas extensas deben dividirse en
  mosaicos.
- El procesamiento depende de la disponibilidad del servicio y de una cuenta
  autenticada.

**Pendientes**
- Integrar la frontera entre ambos entornos en el flujo de trabajo: la
  primera regla del flujo descarga las escenas como archivos locales, de modo
  que el resto del procesamiento no dependa de Earth Engine (ADR-0018).

## Referencias

- CONAF (2021). *Chile Forestal*, 399. Corporación Nacional Forestal.
- Gorelick, N. et al. (2017). Google Earth Engine: Planetary-scale geospatial
  analysis for everyone. *Remote Sensing of Environment*, 202, 18–27.
  https://doi.org/10.1016/j.rse.2017.06.031
