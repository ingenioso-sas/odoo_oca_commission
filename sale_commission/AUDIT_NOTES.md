# Audit Notes — sale_commission (Odoo 13)

> Documento de hallazgos de revisión. **Nada fue modificado.** Registrar para corrección futura.
> Fecha de auditoría: 2026-08-06. Revisado contra `odoo13_prueba2` y fuente OCA 13.0.

## Contexto / alcance

Este módulo gestiona **comisiones de vendedores/agentes** (`agent_ids`, `commission_total`,
`sale.commission.mixin`, settlements). Es **diferente e independiente** de
`pos_payment_method_comission`, que cobra comisiones de **métodos de pago** (merchant fees).
No hay colisión técnica de campos, pero sí **ambigüedad en la UI** (ver hallazgo 1).

## Hallazgos

### 1. 🟠 Ambigüedad de etiquetas en la UI — "Commissions"
`models/account_move.py:14` y `models/sale_order.py:16` usan `string="Commissions"` para
`commission_total`, y la vista de factura agrupa bajo "Commissions"
(`views/account_move_views.xml`). Un usuario no puede distinguir si esas comisiones son de
agente/vendedor o de método de pago.

**Sugerencia**: usar etiqueta explícita `"Sales commissions"` / `"Agent commissions"` en
campos y vistas, de forma coherente con `pos_payment_method_comission` (que usa
"Payment Commission").

### 2. 🟠 `_prepare_invoice` usa `Form()` en un modelo (patrón frágil)
`models/settlement.py:100-132`. Construir un `account.move` vía `Form()` dentro de un método
de modelo es frágil (depende del contexto UI, campos de la vista, etc.). Se recomienda
construir el diccionario de valores directamente (`_prepare_invoice_line`/`create`).

### 3. 🟠 `fields_view_get` con inyección de contexto vía `etree`
`models/account_move.py:42-62`. Manipular `arch` con `etree` para inyectar
`{'partner_id': partner_id, ...}` en el contexto de `invoice_line_ids` es un hack frágil
que puede romper con vistas heredadas o en Odoo 14+.

### 4. 🟡 Código comentado y muerto
- `models/sale_order.py:41-47`: método `_prepare_invoice_line` comentado (dead code).
- `models/settlement.py:50-53`: campo `invoice_id` marcado `# TODO: To be removed`.

### 5. 🟡 `_compute_agent_ids` resetea agentes de TODOS los registros
`models/account_move.py:85-94` y `models/sale_order.py:32-39`:
`self.agent_ids = False` se ejecuta sobre todo el recordset, **incluidos** los que quedan
fuera del `filtered(...)`. Si un usuario asignó agentes manualmente a una línea sin partner
(o de tipo `in_`), se perderían en cada recálculo.

### 6. 🟡 Validación de compañía débil en settlement lines
`models/settlement.py:214-219`: `_check_company` solo verifica `agent_line.company_id`
pero `company_id` del settlement deriva de `settlement_id.company_id`. Podría validarse en
el momento de la asignación del `agent_line`.

### 7. 🟡 `make_invoices` con `groupby` sobre recordsets
`models/settlement.py:140-171`: `groupby` sobre `self.sorted(...)` con `union()` es
funcional pero difícil de mantener y puede ser frágil ante muchos settlements.

### 8. 🟢 Sin hallazgos críticos de seguridad
`security/ir.model.access.csv` y `security/sale_commission_security.xml` definen los grupos
de agente y manager. Se recomienda revisar que `group_sale_salesman_all_leads` u otros
grupos no tengan permisos de escritura no deseados sobre settlements en producciones con
muchos usuarios (revisión manual pendiente).

## Notas de integración

- **No interfiere con `pos_payment_method_comission`**: los campos `commission` /
  `commission_total` / `agent_ids` viven en modelos distintos (`pos.payment` vs
  `account.move` / `sale.order`).
- `pos_orderline_salesperson` (addons_zeinab) **depende** de este módulo.

## Estado

- [x] Corregir etiquetas "Commissions" → explícitas (hallazgo 1) — **2026-08-06**:
  - `commission_total` movido a **después de `amount_residual`** en `views/account_move_views.xml`
    (factura), con etiqueta "Sales commission (not included in total)", `class="text-muted"`
    y oculto si es 0.
  - `views/sale_order_view.xml` (orden de venta): misma corrección de etiqueta/estilo después
    de `amount_total`.
- [x] Refactor `_prepare_invoice` para no usar `Form()` (hallazgo 2) — **2026-10-09 (v13.0.1.9.0)**
- [x] Eliminar dead code (hallazgo 4) — **2026-10-09 (v13.0.1.9.0)**
- [x] Evaluar `_compute_agent_ids` para no resetear agentes manuales (hallazgo 5) — **2026-10-09 (v13.0.1.9.0)**

## Correcciones aplicadas 2026-10-09 — versión 13.0.1.9.0

Verificado en `odoo13_prueba2` (módulo `installed`, `latest_version=13.0.1.9.0`,
smoke 19/19 OK: SO→factura, post, settle, make_invoices, menús).

1. `models/settlement.py`: eliminado `from odoo.tests.common import Form`.
   `_prepare_invoice` construye el `dict` directamente
   (`_prepare_invoice_line_vals`: cuenta de gasto del producto/categoría,
   impuestos proveedor, `settlement_id`, período con formato de idioma).
   `_post_process_line(line_vals)` ahora recibe `dict`
   (compatible con `Form` en el override).
   `exceptions.Warning` → `UserError`; eliminado `"view_type"` del action.
2. `sale_commission_delegated_partner`: `_post_process_line` adaptado a `dict`
   (con fallback a `Form`).
3. `models/account_move.py` / `sale_order.py`: `commission_total`
   `string="Sales commission"` en el modelo; vista de pedido unificada a
   `"Sales commission (not included in total)"` (antes decía "Salesperson...").
   Grupo de líneas renombrado a "Sales commissions".
4. `models/account_move.py::fields_view_get`: `etree.tostring(..., encoding="unicode")`
   (antes devolvía `bytes`) e inyección de `partner_id` idempotente.
5. `_compute_agent_ids` (factura y pedido): por registro, preserva agentes
   manuales; `recompute_agents()` limpia y regenera a pedido explícito.
6. `models/sale_order.py`: restaurado `_prepare_invoice_line` (propaga
   `agent_ids` del pedido a la factura; el compute de factura los respeta).
7. `models/account_move.py`: `_check_settle_integrity` (constrains que
   disparaba en recomputes) reemplazado por override de `write()` que solo
   bloquea modificaciones reales de `agent_id`/`amount` en líneas liquidadas
   (comparación pre-escritura con `float_compare`). Protege igual en producción
   y no genera falsos positivos en recomputes/lecturas.
8. `security/ir.model.access.csv`: corregido `id` duplicado
   (`access_sale_order_line_agent` ×2 → `..._user` el segundo); endurecidos
   permisos (tipos de comisión y report solo lectura para salesman/user;
   settlements sin `unlink` para salesman/user; report SQL `1,0,0,0`).
9. `security/sale_commission_security.xml`: añadida regla multi-company para
   `sale.commission.settlement.line` (+ `company_id` con `store=True` en el modelo).
10. `views/sale_commission_view.xml`: menú movido de `hr.menu_hr_root`
    (sin dependencia de `hr`) a `sale.sale_menu_root` con
    `sales_team.group_sale_manager`.
11. `views/res_partner_view.xml`: `colors=` obsoleto → `decoration-danger/muted`.
12. `report/sale_commission_analysis_report_view.xml`: menú `"Carambas"` →
    `"Commission Analysis"` (coincide con `es.po`); filtros `settled` duplicados →
    `settled`/`not_settled`; typos del help (`aget`, `beeing`).
13. `wizard/wizard_settle.py`: fallback mensual si `settlement` inesperado/vacío.
14. `models/res_partner.py`: documentado `"quaterly"` (typo conservado por
    compatibilidad con datos existentes).
15. `models/sale_commission_mixin.py`: eliminado `"view_type"` obsoleto en
    `button_edit_agents`.

Notas:
- `commission_free` existe en `product.product` (related auto a template,
  verificado en BD); no se duplicó el campo.
- `product_id` del mixin coincide en tipo con el de las líneas; sin cambios.
- Tests OCA de `sale_commission` no corren en `odoo13_prueba2` (sin datos demo:
  falta `base.res_partner_2` — preexistente, no regresión); `hr_commission`: 9/9 OK.
