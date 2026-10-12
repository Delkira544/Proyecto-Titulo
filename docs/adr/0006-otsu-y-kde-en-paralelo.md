# ADR-0006: Aplicar umbralización multinivel de Otsu y KDE en paralelo

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-09-29 |
| **Origen** | Fase 1, registrado retroactivamente |
| **Relacionado con** | RF-08, RF-09, RNF-05, OE2, ADR-0002, ADR-0014 |

## Contexto

Una vez decidida la umbralización no supervisada (ADR-0002), existen dos
formulaciones principales para derivar los cortes entre clases:

- **Otsu** determina el corte que minimiza la varianza intraclase de las
  poblaciones resultantes (Otsu, 1979), y admite una extensión multinivel.
- **La estimación de densidad kernel (KDE)** localiza los mínimos locales de
  la densidad estimada y ajusta el ancho de banda hasta que el número de
  mínimos coincide con el número de clases menos uno (Silverman, 1986).

Ambos métodos pueden entregar cortes distintos sobre la misma distribución, y
no hay evidencia previa que indique cuál se comporta mejor con índices de
severidad en el Biobío.

## Opciones consideradas

1. **Solo Otsu.** *Ventaja:* método estándar y determinista.
   *Limitación:* no verifica la sensibilidad del resultado al algoritmo.
2. **Solo KDE.** *Ventaja:* localiza directamente la separación entre modas.
   *Limitación:* sensible a la elección del ancho de banda.
3. **Ambos en paralelo.** *Ventaja:* la concordancia entre métodos aporta
   respaldo al umbral. *Limitación:* duplica el procesamiento.

## Decisión

Se aplican ambos métodos en paralelo sobre cada combinación de índice y
estrato. El ancho de banda inicial de KDE sigue la regla de Silverman (1986) y
se registra en la configuración (RNF-05). El número de clases lo determina la
correspondencia con las clases de la referencia (ADR-0014).

## Consecuencias

**Positivas**
- Si ambos métodos convergen en valores similares, el umbral tiene mayor
  respaldo que el producido por un solo algoritmo.
- La divergencia entre métodos se convierte en un resultado reportable sobre
  la estabilidad del umbral.

**Negativas**
- Se duplica el costo de la etapa de calibración.

**Pendientes**
- Definir cómo se reporta la concordancia entre métodos (por ejemplo, la
  diferencia absoluta entre cortes) y cuál de los dos alimenta la estrategia
  regional si divergen.

## Referencias

- Otsu, N. (1979). *IEEE Transactions on Systems, Man, and Cybernetics*, 9(1),
  62–66. https://doi.org/10.1109/TSMC.1979.4310076
- Silverman, B. W. (1986). *Density Estimation for Statistics and Data
  Analysis*. Chapman and Hall.
