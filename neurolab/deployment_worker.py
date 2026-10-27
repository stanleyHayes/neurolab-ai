"""Deployment Daemon entrypoint with no HTTP/JWT/provider credential access."""

from .deployment_runtime import configure_replay


def main():
    configure_replay(worker=True)
    from .worker import main as run_worker

    run_worker()


if __name__ == "__main__":
    main()
