import kfp
from kfp import dsl
import kfp.components as comp
from kubernetes.client import V1VolumeMount

base_dir = '../k8s/kfp/components/'

data_validation_op = comp.load_component_from_file(base_dir + 'gate1_data_validation.yaml')
train_op = comp.load_component_from_file(base_dir + 'train.yaml')
train_dp_op = comp.load_component_from_file(base_dir + 'train_dp.yaml')
model_validation_op = comp.load_component_from_file(base_dir + 'gate3_model_validation.yaml')
sign_model_op = comp.load_component_from_file(base_dir + 'gate4_sign_model.yaml')
verify_signature_op = comp.load_component_from_file(base_dir + 'gate4_verify_signature.yaml')
register_model_op = comp.load_component_from_file(base_dir + 'register_model.yaml')

@dsl.pipeline(
    name='CIFAR-10 Secure Training Pipeline',
    description='Обучение модели с проверками безопасности (Data Validation, DP, Model Validation, Signing, Registration)'
)
def secure_pipeline(
    data_path: str = '/data/cifar10',
    test_data_path: str = '/data/cifar10_test.npz',
    epochs: int = 5,
    batch_size: int = 64,
    learning_rate: float = 0.001,
    enable_dp: bool = False,
    noise_multiplier: float = 1.0,
    max_grad_norm: float = 1.0,
    delta: float = 1e-5,
    accuracy_threshold: float = 0.7,
    private_key_path: str = '/mnt/secrets/private.pem',
    public_key_path: str = '/mnt/secrets/public.pem'
):
    secret_volume = dsl.VolumeOp(
        name='create-secret-volume',
        resource_name='model-signing-keys',
        size='1Gi',
        storage_class='standard'
    )

    validation = data_validation_op(
        data_path=data_path,
        threshold_sigma=3.0,
        label_col='label'
    )

    with dsl.Condition(validation.outputs['passed'] == True):
        if enable_dp:
            train = train_dp_op(
                data_path=data_path,
                epochs=epochs,
                batch_size=batch_size,
                learning_rate=learning_rate,
                noise_multiplier=noise_multiplier,
                max_grad_norm=max_grad_norm,
                delta=delta
            )
        else:
            train = train_op(
                data_path=data_path,
                epochs=epochs,
                batch_size=batch_size,
                learning_rate=learning_rate
            )

        model_check = model_validation_op(
            model_uri=train.outputs['model_uri'],
            test_data=test_data_path,
            accuracy_threshold=accuracy_threshold
        )

        with dsl.Condition(model_check.outputs['passed'] == True):
            sign = sign_model_op(
                model_uri=train.outputs['model_uri'],
                private_key=private_key_path
            )
            sign.add_volume(secret_volume.volume)
            sign.add_volume_mount(
                V1VolumeMount(
                    mount_path='/mnt/secrets',
                    name=secret_volume.volume.name
                )
            )

            verify = verify_signature_op(
                model_uri=train.outputs['model_uri'],
                signature_file=sign.outputs['signature_file'],
                public_key=public_key_path
            )
            verify.add_volume(secret_volume.volume)
            verify.add_volume_mount(
                V1VolumeMount(
                    mount_path='/mnt/secrets',
                    name=secret_volume.volume.name
                )
            )

            with dsl.Condition(verify.outputs['passed'] == True):
                register = register_model_op(
                    model_uri=train.outputs['model_uri'],
                    stage='Staging'
                )

if __name__ == '__main__':
    from kfp import compiler
    compiler.Compiler().compile(secure_pipeline, 'secure_pipeline.tar.gz')
