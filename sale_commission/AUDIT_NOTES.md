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
- [ ] Refactor `_prepare_invoice` para no usar `Form()` (hallazgo 2)
- [ ] Eliminar dead code (hallazgo 4)
- [ ] Evaluar `_compute_agent_ids` para no resetear agentes manuales (hallazgo 5)
