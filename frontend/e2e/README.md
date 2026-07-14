# Browser seam

The role-based seam runs against a running frontend with authenticated Playwright storage states:

```bash
E2E_BASE_URL=http://localhost:3000 \
E2E_HR_STORAGE_STATE=/absolute/path/hr.json \
E2E_EMPLOYEE_STORAGE_STATE=/absolute/path/employee.json \
pnpm test:e2e
```

The config creates four projects: HR and Employee Account at desktop (1280px) and mobile (390px). Tests use accessible roles and visible behavior rather than private component details. Failures retain a trace, screenshot, and video; console errors are asserted in the reviewed flows.
