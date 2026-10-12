# ADR-0004: Usar la colección armonizada de Sentinel-2 y fijar los identificadores de escena

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-09-29 |
| **Origen** | Revisión posterior a la Fase 1 |
| **Relacionado con** | RNF-12, RF-01, RF-03a, OE1, OE2, OE3 |

## Contexto

Desde el 25 de enero de 2022, las escenas de Sentinel-2 procesadas con la
línea base 04.00 o posterior incorporan un desplazamiento en sus valores de
reflectancia. El conjunto de calibración abarca incendios entre 2020 y 2025,
es decir, escenas anteriores y posteriores a ese cambio.

Si no se corrige, los valores de dNBR de ambos períodos no son comparables, y
los umbrales regionales mezclarían escalas distintas. Además, el catálogo de
Earth Engine puede cambiar con el tiempo, lo que afecta la reproducibilidad
si no se registra exactamente qué escenas se usaron.

## Opciones consideradas

1. **Colección `COPERNICUS/S2_SR` sin corrección.**
   *Limitación:* produce valores no comparables entre períodos.
2. **Colección `COPERNICUS/S2_SR` con corrección manual del desplazamiento.**
   *Ventaja:* control explícito. *Limitación:* exige identificar la línea
   base de cada escena y replicar una corrección que ya existe.
3. **Colección `COPERNICUS/S2_SR_HARMONIZED`, con los identificadores de cada
   escena registrados en la configuración.**
   *Ventaja:* corrige el desplazamiento de forma estandarizada y fija las
   escenas exactas. *Limitación:* depende de la armonización provista por la
   plataforma.

## Decisión

Se adopta la opción 3. Todas las escenas se obtienen de
`COPERNICUS/S2_SR_HARMONIZED`, y el identificador de cada una se registra en
el archivo de configuración.

## Consecuencias

**Positivas**
- Los valores de los índices son comparables en todo el período de
  calibración.
- Cualquier ejecución futura usa exactamente las mismas escenas, aunque el
  catálogo cambie.

**Negativas**
- El resultado depende de la corrección aplicada por la plataforma.

**Pendientes**
- Verificar que todas las escenas seleccionadas estén disponibles en la
  colección armonizada.

## Referencias

- Google Earth Engine. *Harmonized Sentinel-2 MSI: MultiSpectral Instrument,
  Level-2A*.
  https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED
