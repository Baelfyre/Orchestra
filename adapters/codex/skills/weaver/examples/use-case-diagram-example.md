# Weaver Quick Diagram Plan

## Diagram Needed
- UML use case diagram for payroll access.

## Objective
- Show which confirmed roles can generate and view payroll records.

## Inputs Required
- Approved role-permission requirements.

## Recommended Format
- PlantUML

## Draft Diagram

```plantuml
@startuml
left to right direction
actor "Payroll Administrator" as Admin
actor "Employee" as Employee
rectangle "Payroll System" {
  usecase "Generate Payroll" as Generate
  usecase "View Own Payslip" as ViewOwn
}
Admin --> Generate
Employee --> ViewOwn
@enduml
```

## Missing Evidence
- Whether HR shares payroll-administrator permissions
- Whether payslip download is a separate user goal
