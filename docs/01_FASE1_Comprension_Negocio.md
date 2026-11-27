# 01 — Fase 1: Comprensión del Negocio (CRISP-DM)

## 1. Contexto del Negocio
**NovaMarket Perú** es una tienda multirubro en línea (estilo Amazon: artículos de hogar, oficina, regalos, decoración y accesorios) que atiende compras minoristas y por volumen en **Soles (PEN) y Dólares (USD)**.

Los sistemas de ventas convencionales solo suman totales del mes (BI), pero desaprovechan el historial de miles de boletas para aumentar ventas en caja y evitar que los clientes dejen de volver.

---

## 2. Objetivos de Negocio y Minería de Datos

### 2.1 Objetivo del Sistema (Negocio)
1. Proveer una aplicación web comercial donde el usuario/vendedor pueda **buscar productos, armar un carrito, cotizar con tipo de cambio USD→PEN real y guardar boletas en SQLite**.
2. Aumentar el ticket promedio sugiriendo en vivo productos complementarios al carrito (*venta cruzada*).
3. Retener clientes identificando su segmento (**VIP / Leal / En Riesgo / Nuevo**) y si tienen probabilidad de abandonar la tienda.

### 2.2 Objetivos Técnicos de Minería de Datos
1. **Reglas de Asociación (No supervisado):** Extraer pares `Producto A → Producto B` desde boletas reales usando **Soporte**, **Confianza** y **Lift > 1.2** para recomendar complementos sin reglas escritas a mano.
2. **Segmentación RFM (Clustering `K-Means`) + Predicción de Recompra/Fuga (Clasificación supervisada):**
   * Agrupar clientes por *Recencia, Frecuencia y Monto*.
   * Predecir sobre una partición temporal estricta si un cliente volverá a comprar en el trimestre siguiente, con criterio mínimo **`ROC-AUC ≥ 0.78`** y explicabilidad **SHAP**.
