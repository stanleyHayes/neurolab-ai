.PHONY: lint test validate quality build sonar sonar-up sonar-down

PYTHON ?= python3
SONAR_PROJECT_KEY ?= neurolab-ai
SONAR_ORGANIZATION ?=
SONAR_HOST_URL ?= http://localhost:9000
SONAR_ARGS = -Dsonar.host.url="$(SONAR_HOST_URL)" -Dsonar.projectKey="$(SONAR_PROJECT_KEY)"

ifneq ($(strip $(SONAR_ORGANIZATION)),)
SONAR_ARGS += -Dsonar.organization="$(SONAR_ORGANIZATION)"
endif

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .
	npm run lint
	npm run typecheck

build:
	npm run build

test:
	$(PYTHON) -m coverage run --source=neurolab,scripts -m unittest discover -s tests -v
	$(PYTHON) -m coverage xml -o coverage/python.xml
	npm test

validate:
	$(PYTHON) scripts/audit_datasets.py
	$(PYTHON) -m py_compile neurolab/*.py scripts/*.py tests/*.py

quality: lint test validate build

sonar:
	@test -n "$${SONAR_TOKEN:-}" || (echo "Set SONAR_TOKEN from your local SonarQube account before running analysis." >&2; exit 1)
	$(MAKE) quality
	sonar-scanner $(SONAR_ARGS)

sonar-up:
	docker compose -f compose.sonarqube.yml up -d

sonar-down:
	docker compose -f compose.sonarqube.yml down