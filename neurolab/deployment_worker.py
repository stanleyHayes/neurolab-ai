"""Deployment worker without signing credentials; verified Meta is explicit opt-in."""

from .deployment_runtime import configure_deployment


def main():
    configure_deployment(worker=True)
    from .worker import main as run_worker

    run_worker()


if __name__ == "__main__":
    main()
