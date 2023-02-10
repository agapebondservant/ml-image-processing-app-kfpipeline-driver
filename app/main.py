import kfp.dsl as dsl
from kfp import Client
import logging
import warnings
import utils

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
warnings.filterwarnings('ignore')


@dsl.pipeline(
    name='cifar_cnn_kfp',
    description='Pipeline which trains and serves a CNN model using Keras.'
)
def cifar_pipeline():
    # Upload Dataset
    upload_dataset = dsl.ContainerOp(
        name='upload_dataset',
        image='oawofolu/ml-image-processor',
        command="python",
        arguments=[
            "/app/main.py",
            "--mlflow_entry", 'upload_dataset',
            "--mlflow_stage", utils.get_env_var('MLFLOW_STAGE'),
            "--git_repo", utils.get_env_var('GIT_REPO'),
            "--experiment_name", utils.get_env_var('EXPERIMENT_NAME'),
            "--environment_name", utils.get_env_var('ENVIRONMENT_NAME')
        ]
    )

    # Train Model
    train_model = dsl.ContainerOp(
        name='train_model',
        image='oawofolu/ml-image-processor',
        command="python",
        arguments=[
            "/app/main.py",
            "--mlflow_entry", 'train_model',
            "--mlflow_stage", utils.get_env_var('MLFLOW_STAGE'),
            "--git_repo", utils.get_env_var('GIT_REPO'),
            "--experiment_name", utils.get_env_var('EXPERIMENT_NAME'),
            "--environment_name", utils.get_env_var('ENVIRONMENT_NAME')
        ]
    )
    train_model.after(upload_dataset)

    # Evaluate Model
    evaluate_model = dsl.ContainerOp(
        name='evaluate_model',
        image='oawofolu/ml-image-processor',
        command="python",
        arguments=[
            "/app/main.py",
            "--mlflow_entry", 'evaluate_model',
            "--mlflow_stage", utils.get_env_var('MLFLOW_STAGE'),
            "--git_repo", utils.get_env_var('GIT_REPO'),
            "--experiment_name", utils.get_env_var('EXPERIMENT_NAME'),
            "--environment_name", utils.get_env_var('ENVIRONMENT_NAME')
        ]
    )
    evaluate_model.after(train_model)

    # Promote Model to Staging
    promote_model_to_staging = dsl.ContainerOp(
        name='promote_model_to_staging',
        image='oawofolu/ml-image-processor',
        command="python",
        arguments=[
            "/app/main.py",
            "--mlflow_entry", 'promote_model_to_staging',
            "--mlflow_stage", utils.get_env_var('MLFLOW_STAGE'),
            "--git_repo", utils.get_env_var('GIT_REPO'),
            "--experiment_name", utils.get_env_var('EXPERIMENT_NAME'),
            "--environment_name", utils.get_env_var('ENVIRONMENT_NAME')
        ]
    )
    promote_model_to_staging.after(evaluate_model)

    # steps = [upload_dataset, train_model, evaluate_model, promote_model_to_staging]
    # for step in steps:
    #    step.apply(onprem.mount_pvc(pvc_name, 'local-storage', '/mnt'))


if __name__ == '__main__':
    logging.info(f"Compiling Kubeflow pipeline...host={utils.get_env_var('KUBEFLOW_PIPELINES_HOST')}")
    import kfp.compiler as compiler
    compiler.Compiler().compile(cifar_pipeline, __file__ + '.zip')

    logging.info("Generating new experiment run...")
    client = Client(host=f'{utils.get_env_var("KUBEFLOW_PIPELINES_HOST")}')
    cifar_experiment = client.create_experiment(name=utils.get_env_var('EXPERIMENT_NAME'))
    cifar_run = client.run_pipeline(cifar_experiment.id, 'cifar-pipeline', __file__ + '.zip')
    logging.info("Run completed.")
