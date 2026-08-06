# Audit Notes — hr_commission (Odoo 13)

> Documento de hallazgos de revisión. **Nada fue modificado.** Registrar para corrección futura.
> Fecha de auditoría: 2026-08-06. Revisado contra `odoo13_prueba2`.

## Contexto / alcance

Módulo OCA que integra `sale_commission` con RRHH: permite marcar un `res.partner` como
agente tipo "salesman (employee)" y enlazarlo a un `hr.employee`. Genera/valida agentes de
vendedor. **No tiene relación con comisiones de métodos de pago.**

## Hallazgos

### 1. 🟠 Lógica de `hr.employee.write` puede bloquear ediciones legítimas
`models/hr_employee.py:57-68`. El guard:

```python
if not vals.get("user_id"):
    salesmen = self.mapped("user_id.partner_id").filtered(...)
    if salesmen:
        raise ValidationError(...)
```

Intenta impedir **quitar** el usuario de un empleado con agente salesman, pero la condición
`not vals.get("user_id")` también se dispara cuando `user_id` **no se toca** en el `write`
(p. ej. editar el nombre o teléfono). Eso haría que cualquier `write` sobre un empleado con
agente salesman falle si no se pasa `user_id` en el dict.

**Sugerencia**: detectar explícitamente la remoción, p. ej.
```python
if vals.get("user_id") is False and self.mapped("user_id.partner_id").filtered(...):
    raise ValidationError(...)
```

### 2. 🟡 `write` sobre `agent_ids` en empleado no está protegido
No hay protección para el caso inverso: borrar el `employee_id` de un agente, o cambiar el
agente a otro empleado, mientras hay líneas/settlements pendientes. Solo se valida al quitar
`user_id`.

### 3. 🟡 `_get_or_create_commission` toma la primera comisión de la base
`models/hr_employee.py:20-25`: `search([], limit=1)` siempre asigna la **primera**
`sale.commission` del sistema como default al crear un agente. Con varias comisiones
configuradas puede ser incorrecto; convendría permitir elegir o usar la del plan de comisión
del empleado si existe.

### 4. 🟡 `_check_employee` solo se dispara con `agent_type`
`models/res_partner.py:38-50`. Si un partner es marcado `agent=True` y `salesman` pero se
asigna/elimina `employee_id` después, la validación "there must be one employee linked" no
se reevalúa (constraint solo en `agent_type`). Evaluar `@api.constrains("agent", "agent_type", "employee_id")`.

### 5. 🟡 `_compute_employee` mezcla lógica super/override
`models/res_partner.py:26-36`: usa `hasattr(super(), "_compute_employee")` para llamar a la
implementación heredada. Esto es frágil (depende de si existe o no en el MRO) y poco
idiomático; mejor implementar la super directamente y sobreescribir el campo relacionado.

### 6. 🟢 Nota de interoperabilidad
Define `agent_type` salesman y `employee_id` en `res.partner`, usados por
`pos_orderline_salesperson` (`employee_salesperson_ids` filtra `agent_ids.agent_type =
'salesman'`). No colisiona con `pos_payment_method_comission`.

## Estado

- [ ] Corregir `hr.employee.write` para no bloquear ediciones sin `user_id` (hallazgo 1)
- [ ] Evaluar validaciones cruzadas agente↔empleado (hallazgo 2 y 4)
- [ ] Revisar `_get_or_create_commission` default (hallazgo 3)
