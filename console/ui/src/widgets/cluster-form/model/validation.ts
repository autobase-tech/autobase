import { TFunction } from 'i18next';
import * as yup from 'yup';
import { CLUSTER_FORM_FIELD_NAMES } from '@widgets/cluster-form/model/constants.ts';
import { PROVIDERS } from '@shared/config/constants.ts';
import { AUTHENTICATION_METHODS, IS_EXPERT_MODE } from '@shared/model/constants.ts';
import ipRegex from 'ip-regex';
import { SECRET_MODAL_CONTENT_FORM_FIELD_NAMES } from '@entities/secret-form-block/model/constants.ts';
import { BackupsBlockFormSchema } from '@entities/cluster/expert-mode/backups-block/model/validation.ts';
import { DatabasesBlockSchema } from '@entities/cluster/expert-mode/databases-block/model/validation.ts';
import { ConnectionPoolsBlockSchema } from '@entities/cluster/expert-mode/connection-pools-block/model/validation.ts';
import { PostgresParametersBlockFormSchema } from '@entities/cluster/expert-mode/postgres-parameters-block/model/validation.ts';
import { KernelParametersBlockFormSchema } from '@entities/cluster/expert-mode/kernel-parameters-block/model/validation.ts';
import { AdditionalSettingsBlockFormSchema } from '@entities/cluster/expert-mode/additional-settings-block/model/validation.ts';
import { INSTANCES_BLOCK_FIELD_NAMES } from '@entities/cluster/instances-block/model/const.ts';
import { STORAGE_BLOCK_FIELDS } from '@entities/cluster/storage-block/model/const.ts';
import { DatabaseServersBlockSchema } from '@entities/cluster/database-servers-block/model/validation.ts';
import { SSH_KEY_BLOCK_FIELD_NAMES } from '@entities/cluster/ssh-key-block/model/const.ts';
import { LoadBalancerBlockSchema } from '@entities/cluster/load-balancers-block/model/validation.ts';
import { DcsBlockSchema } from '@entities/cluster/expert-mode/dcs-block/model/validation.ts';
import { isValidSshPublicKeyList } from '@shared/lib/sshPublicKeyValidation.ts';
import { isValidSshPrivateKey } from '@shared/lib/sshPrivateKeyValidation.ts';

const CloudFormSchema = (t: TFunction) =>
  yup.object({
    [CLUSTER_FORM_FIELD_NAMES.REGION]: yup
      .mixed()
      .when(CLUSTER_FORM_FIELD_NAMES.PROVIDER, ([provider], schema) =>
        provider?.code !== PROVIDERS.LOCAL ? yup.string().required() : schema.notRequired(),
      ),
    [CLUSTER_FORM_FIELD_NAMES.REGION_CONFIG]: yup
      .mixed()
      .when(CLUSTER_FORM_FIELD_NAMES.PROVIDER, ([provider], schema) =>
        provider?.code !== PROVIDERS.LOCAL
          ? yup
              .object({
                code: yup.string(),
                location: yup.string(),
              })
              .required()
          : schema.notRequired(),
      ),
    [INSTANCES_BLOCK_FIELD_NAMES.INSTANCE_TYPE]: yup
      .mixed()
      .when(CLUSTER_FORM_FIELD_NAMES.PROVIDER, ([provider], schema) =>
        provider?.code !== PROVIDERS.LOCAL ? yup.string().required() : schema.notRequired(),
      ),
    [CLUSTER_FORM_FIELD_NAMES.INSTANCE_CONFIG]: yup
      .mixed()
      .when(CLUSTER_FORM_FIELD_NAMES.PROVIDER, ([provider], schema) =>
        provider?.code !== PROVIDERS.LOCAL
          ? yup
              .object({
                code: yup.string(),
                cpu: yup.number(),
                shared_cpu: yup.boolean(),
                currency: yup.string(),
                price_hourly: yup.number(),
                price_monthly: yup.number(),
                ram: yup.number(),
              })
              .required()
          : schema.notRequired(),
      ),
    [CLUSTER_FORM_FIELD_NAMES.INSTANCES_AMOUNT]: yup
      .mixed()
      .when(CLUSTER_FORM_FIELD_NAMES.PROVIDER, ([provider], schema) =>
        provider?.code !== PROVIDERS.LOCAL ? yup.number().required() : schema.notRequired(),
      ),
    [STORAGE_BLOCK_FIELDS.STORAGE_AMOUNT]: yup
      .mixed()
      .when(CLUSTER_FORM_FIELD_NAMES.PROVIDER, ([provider], schema) =>
        provider?.code !== PROVIDERS.LOCAL ? yup.number().required() : schema.notRequired(),
      ),
    [SSH_KEY_BLOCK_FIELD_NAMES.SSH_PUBLIC_KEY]: yup
      .mixed()
      .when(CLUSTER_FORM_FIELD_NAMES.PROVIDER, ([provider], schema) =>
        provider?.code !== PROVIDERS.LOCAL
          ? yup
              .string()
              .required(t('requiredField', { ns: 'validation' }))
              .test(
                'is valid SSH public key',
                t('invalidSshPublicKey', { ns: 'validation' }),
                (value) => !value || isValidSshPublicKeyList(value),
              )
          : schema.notRequired(),
      ),
  });

export const LocalFormSchema = (t: TFunction) =>
  yup
    .object({
      [CLUSTER_FORM_FIELD_NAMES.AUTHENTICATION_METHOD]: yup
        .mixed()
        .when(CLUSTER_FORM_FIELD_NAMES.PROVIDER, ([provider], schema) =>
          provider?.code === PROVIDERS.LOCAL ? yup.string().required() : schema.notRequired(),
        ),
      [SECRET_MODAL_CONTENT_FORM_FIELD_NAMES.SSH_PRIVATE_KEY]: yup
        .mixed()
        .when(
          [CLUSTER_FORM_FIELD_NAMES.PROVIDER, CLUSTER_FORM_FIELD_NAMES.AUTHENTICATION_METHOD],
          ([provider, authenticationMethod], schema) =>
            provider?.code === PROVIDERS.LOCAL && authenticationMethod === AUTHENTICATION_METHODS.SSH
              ? yup
                  .mixed()
                  .when(CLUSTER_FORM_FIELD_NAMES.IS_USE_DEFINED_SECRET, ([isUseDefinedSecret], schema) =>
                    !isUseDefinedSecret
                      ? yup
                          .string()
                          .required(t('requiredField', { ns: 'validation' }))
                          .test(
                            'is valid SSH private key',
                            t('invalidSshPrivateKey', { ns: 'validation' }),
                            (value) => !value || isValidSshPrivateKey(value),
                          )
                      : schema.notRequired(),
                  )
              : schema.notRequired(),
        ),
      [SECRET_MODAL_CONTENT_FORM_FIELD_NAMES.USERNAME]: yup
        .mixed()
        .when(
          [
            CLUSTER_FORM_FIELD_NAMES.PROVIDER,
            CLUSTER_FORM_FIELD_NAMES.AUTHENTICATION_METHOD,
            CLUSTER_FORM_FIELD_NAMES.IS_USE_DEFINED_SECRET,
          ],
          ([provider, authenticationMethod, isUseDefinedSecret], schema) =>
            provider?.code === PROVIDERS.LOCAL &&
            (authenticationMethod === AUTHENTICATION_METHODS.SSH ||
              (authenticationMethod === AUTHENTICATION_METHODS.PASSWORD && !isUseDefinedSecret))
              ? yup.string().required(t('requiredField', { ns: 'validation' }))
              : schema.notRequired(),
        ),
      [SECRET_MODAL_CONTENT_FORM_FIELD_NAMES.PASSWORD]: yup
        .mixed()
        .when(
          [CLUSTER_FORM_FIELD_NAMES.PROVIDER, CLUSTER_FORM_FIELD_NAMES.AUTHENTICATION_METHOD],
          ([provider, authenticationMethod], schema) =>
            provider?.code === PROVIDERS.LOCAL && authenticationMethod === AUTHENTICATION_METHODS.PASSWORD
              ? yup
                  .mixed()
                  .when(CLUSTER_FORM_FIELD_NAMES.IS_USE_DEFINED_SECRET, ([isUseDefinedSecret], schema) =>
                    !isUseDefinedSecret
                      ? yup.string().required(t('requiredField', { ns: 'validation' }))
                      : schema.notRequired(),
                  )
              : schema.notRequired(),
        ),
      [CLUSTER_FORM_FIELD_NAMES.AUTHENTICATION_IS_SAVE_TO_CONSOLE]: yup
        .mixed()
        .when(
          [CLUSTER_FORM_FIELD_NAMES.PROVIDER, CLUSTER_FORM_FIELD_NAMES.IS_USE_DEFINED_SECRET],
          ([provider, isUseDefinedSecret], schema) =>
            provider?.code === PROVIDERS.LOCAL && !isUseDefinedSecret ? yup.boolean() : schema.notRequired(),
        ),
      [CLUSTER_FORM_FIELD_NAMES.SECRET_KEY_NAME]: yup
        .mixed()
        .when(
          [CLUSTER_FORM_FIELD_NAMES.PROVIDER, CLUSTER_FORM_FIELD_NAMES.AUTHENTICATION_IS_SAVE_TO_CONSOLE],
          ([provider, isSaveToConsole], schema) =>
            provider?.code === PROVIDERS.LOCAL && isSaveToConsole
              ? yup.string().required(t('requiredField', { ns: 'validation' }))
              : schema.notRequired(),
        ),
      [CLUSTER_FORM_FIELD_NAMES.CLUSTER_VIP_ADDRESS]: yup
        .mixed()
        .when(CLUSTER_FORM_FIELD_NAMES.PROVIDER, ([provider], schema) =>
          provider?.code === PROVIDERS.LOCAL
            ? yup
                .string()
                .test(
                  'should be a correct VIP address',
                  t('shouldBeACorrectV4Ip', { ns: 'validation' }),
                  (value) => !value || ipRegex.v4({ exact: true }).test(value),
                )
            : schema.notRequired(),
        ),
      [CLUSTER_FORM_FIELD_NAMES.IS_USE_DEFINED_SECRET]: yup
        .mixed()
        .when([CLUSTER_FORM_FIELD_NAMES.PROVIDER], ([provider], schema) =>
          provider?.code === PROVIDERS.LOCAL ? yup.boolean().optional() : schema.notRequired(),
        ),
      [CLUSTER_FORM_FIELD_NAMES.SECRET_ID]: yup
        .mixed()
        .when(
          [CLUSTER_FORM_FIELD_NAMES.PROVIDER, CLUSTER_FORM_FIELD_NAMES.IS_USE_DEFINED_SECRET],
          ([provider, isUseDefinedSecret], schema) =>
            provider?.code === PROVIDERS.LOCAL && isUseDefinedSecret
              ? yup.string().required(t('requiredField', { ns: 'validation' }))
              : schema.notRequired(),
        ),
    })
    .concat(DatabaseServersBlockSchema(t))
    .concat(LoadBalancerBlockSchema(t))
    .concat(DcsBlockSchema(t));

export const ClusterFormSchema = (t: TFunction) => {
  const defaultSchema = yup
    .object({
      [CLUSTER_FORM_FIELD_NAMES.PROVIDER]: yup.object().required(),
      [CLUSTER_FORM_FIELD_NAMES.ENVIRONMENT_ID]: yup.number(),
      [CLUSTER_FORM_FIELD_NAMES.CLUSTER_NAME]: yup
        .string()
        .test('clusters should have proper naming', t('clusterShouldHaveProperNaming', { ns: 'validation' }), (value) =>
          value.match(/^[a-z0-9][a-z0-9-]{0,20}$/g),
        )
        .required(t('requiredField', { ns: 'validation' })),
      [CLUSTER_FORM_FIELD_NAMES.DESCRIPTION]: yup.string(),
      [CLUSTER_FORM_FIELD_NAMES.POSTGRES_VERSION]: yup.number().required(t('requiredField', { ns: 'validation' })),
    })
    .concat(CloudFormSchema(t))
    .concat(LocalFormSchema(t));

  return IS_EXPERT_MODE
    ? defaultSchema
        .concat(DatabasesBlockSchema)
        .concat(ConnectionPoolsBlockSchema(t))
        .concat(BackupsBlockFormSchema(t))
        .concat(PostgresParametersBlockFormSchema(t))
        .concat(KernelParametersBlockFormSchema(t))
        .concat(AdditionalSettingsBlockFormSchema(t))
    : defaultSchema;
};
