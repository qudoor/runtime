from typing import Dict

PageNumQueryKey = "pageNum"
PageSizeQueryKey = "pageSize"

BatchOperationUpdate = "update"
BatchOperationCreate = "create"
BatchOperationDelete = "delete"

LocalRepositoryDomainName = "registry.kubeoperator.io"

DefaultResourceName = "kubeoperator"
StatusPending = "Pending"
StatusRunning = "Running"
StatusNotReady = "NotReady"
StatusUpgrading = "Upgrading"
StatusSuccess = "Success"
StatusFailed = "Failed"
StatusLost = "Lost"
StatusCreating = "Creating"
StatusInitializing = "Initializing"
StatusTerminating = "Terminating"
StatusWaiting = "Waiting"
StatusDisabled = "disable"
StatusEnabled = "enable"

ErrorTypeTimeout = "Timeout"
ErrorTypeUnreachable = "unreachable"
ErrorTypeFailed = "failed"
OKString = 'ok'

TaskCancel = "task cancel"

DefaultPassword = "kubeoperator@admin123"

GetQutrunkPodStatus = 'GetQutrunkPodStatus'
DeployQutrunkEnv = 'DeployQutrunkEnv'
ViewLog = 'ViewLog'
DeleteQutrunkEnv = 'DeleteQutrunkEnv'

DeployQuboxDemoApp = 'DeployQuboxDemoApp'

DeployQufinanceApp = 'DeployQufinanceApp'

Log = 'log'
Detail = 'detail'
Localhost = 'localhost'
Query = 'query'
Create = 'create'
Delete = 'delete'
StatusString = 'status'

StatusRetry = "Retry"
StatusActive = "Active"

ConditionsString = 'conditions'

BACKEND: Dict[str, str] = {
    'BACKEND_TYPE': 'backend_typ_e',
    'AWS_ACCESS_KEY_ID': 'aws_access_key_i_d',
    'AWS_SECRET_ACCESS_KEY': 'aws_secret_access_ke_y',
    'AWS_DEFAULT_REGION': 'aws_default_regio_n'
}

DEFAULT_BACKEND: Dict[str, None] = {
    BACKEND['BACKEND_TYPE']: None,
    BACKEND['AWS_ACCESS_KEY_ID']: None,
    BACKEND['AWS_SECRET_ACCESS_KEY']: None,
    BACKEND['AWS_DEFAULT_REGION']: None,
}

CREDENTIAL_ID = 'credential_id'
CREDENTIAL = 'credential'
