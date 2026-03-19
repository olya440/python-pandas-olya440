from datetime import datetime
from typing import Optional, List
import pandas as pd


class MedicalDevice:
    """Класс для хранения данных об одном медицинском устройстве."""

    def __init__(
        self,
        device_id: str,
        clinic_id: str,
        clinic_name: str,
        city: str,
        department: str,
        model: str,
        serial_number: str,
        install_date: datetime,
        status: str = 'unknown',
        warranty_until: Optional[datetime] = None,
        last_calibration_date: Optional[datetime] = None,
        last_service_date: Optional[datetime] = None,
        issues_reported_12mo: int = 0,
        failure_count_12mo: int = 0,
        uptime_pct: float = 100.0,
        issues_text: Optional[str] = None,
        status_normalized: str = 'unknown',
        warranty_expired: bool = False,
        next_calibration: Optional[datetime] = None,
        calibration_status: str = 'unknown',
        calibration_error: bool = False
    ):
        """Инициализация объекта медицинского устройства.

        Args:
            device_id: Уникальный идентификатор устройства.
            clinic_id: Уникальный идентификатор клиники.
            clinic_name: Название клиники.
            city: Город расположения клиники.
            department: Медицинское отделение клиники.
            model: Модель устройства.
            serial_number: Серийный номер устройства.
            install_date: Дата установки оборудования в клинике.
            status: Текущий статус устройства (по умолчанию 'unknown').
            warranty_until: Дата окончания гарантии производителя (по умолчанию None).
            last_calibration_date: Дата последней калибровки оборудования (по умолчанию None).
            last_service_date: Дата последнего технического обслуживания (по умолчанию None).
            issues_reported_12mo: Количество проблем за последние 12 месяцев (по умолчанию 0).
            failure_count_12mo: Количество отказов за последние 12 месяцев (по умолчанию 0).
            uptime_pct: Процент работоспособности устройства (по умолчанию 100.0).
            issues_text: Текстовое описание проблем (по умолчанию None).
            status_normalized: Нормализованный статус устройства (по умолчанию 'unknown').
            warranty_expired: Флаг истёкшей гарантии (по умолчанию False).
            next_calibration: Дата следующей плановой калибровки (по умолчанию None).
            calibration_status: Статус калибровки устройства (по умолчанию 'unknown').
            calibration_error: Флаг ошибки калибровки (по умолчанию False).
        """

        self.device_id = device_id
        self.clinic_id = clinic_id
        self.clinic_name = clinic_name
        self.city = city
        self.department = department
        self.model = model
        self.serial_number = serial_number
        self.install_date = install_date
        self.warranty_until = warranty_until
        self.last_calibration_date = last_calibration_date
        self.last_service_date = last_service_date
        self.status = status
        self.status_normalized = status_normalized
        self.issues_reported_12mo = issues_reported_12mo
        self.failure_count_12mo = failure_count_12mo
        self.uptime_pct = uptime_pct
        self.issues_text = issues_text
        self.warranty_expired = warranty_expired
        self.calibration_error = calibration_error
        self.next_calibration = next_calibration
        self.calibration_status = calibration_status

    def is_operational(self) -> bool:
        """Проверка: устройство работает.

        Returns:
            True или False.
        """

        return self.status_normalized in ['operational', 'maintenance_scheduled']

    def is_faulty(self) -> bool:
        """Проверка: устройство неисправно.

        Returns:
            True или False.
        """

        return self.status_normalized == 'faulty'

    def is_warranty_valid(self) -> bool:
        """Проверка: гарантия действительна.

        Returns:
            True или False.
        """

        if self.warranty_until is None:
            return True

        return not self.warranty_expired

    def needs_calibration(self) -> bool:
        """Проверка: требуется калибровка.

        Returns:
            True или False.
        """

        return self.calibration_status in ['overdue', 'due_soon', 'no_record']

    def get_problem_score(self) -> float:
        """Расчёт индекса проблемности устройства.

        Returns:
            Индекс проблемности устройства.
        """

        score = 0
        score += self.issues_reported_12mo
        score += self.failure_count_12mo * 2
        if self.is_faulty():
            score += 3
        score += (100 - self.uptime_pct) * 0.5

        return score

def load_data(filepath):
    """Загрузка и первичная обработка данных из Excel.

    Args:
        filepath: Путь к файлу Excel.

    Returns:
        DataFrame.
    """

    df = pd.read_excel(filepath)
    df.columns = df.columns.str.lower()
    df.columns = df.columns.str.strip()
    df = df.drop_duplicates(subset=['device_id'], keep='first')
    print(f"Загружено записей: {len(df)}")

    return df

def normalize_status(df: pd.DataFrame) -> pd.DataFrame:
    """Нормализация статусов устройств.

    Args:
        df: DataFrame.

    Returns:
        Тот же DataFrame с добавленной колонкой 'status_normalized'.
    """

    status_map = {
        'operational': 'operational',
        'ok': 'operational',
        'op': 'operational',
        'working': 'operational',
        'planned_installation': 'planned_installation',
        'planned': 'planned_installation',
        'maintenance_scheduled': 'maintenance_scheduled',
        'maintenance': 'maintenance_scheduled',
        'maint_sched': 'maintenance_scheduled',
        'service_scheduled': 'maintenance_scheduled',
        'faulty': 'faulty',
        'broken': 'faulty',
        'needs_repair': 'faulty',
        'fault': 'faulty',
    }

    df['status_normalized'] = (
        df['status']
        .astype(str)
        .str.lower()
        .str.strip()
        .map(lambda x: status_map.get(x, 'unknown'))
    )

    return df

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """Обрабатывает данные DataFrame: парсит даты и добавляет флаги ошибок.

    Args:
        df: DataFrame.

    Returns:
        Тот же DataFrame с добавленными колонками.
    """
    
    date_cols = [
        'install_date',
        'warranty_until',
        'last_calibration_date',
        'last_service_date',
    ]
    for col in date_cols:
        df[f'{col}_parsed'] = pd.to_datetime(
            df[col], errors='coerce', dayfirst=True
        )

    df['calibration_error'] = (
        df['last_calibration_date_parsed'].notna()
        & df['install_date_parsed'].notna()
        & (df['last_calibration_date_parsed'] < df['install_date_parsed'])
    )

    df['warranty_expired'] = (
        df['warranty_until_parsed'].notna()
        & (df['warranty_until_parsed'] < datetime.now())
    )

    return df

def filter_by_warranty(df: pd.DataFrame) -> pd.DataFrame:
    """Фильтрация устройств по гарантии.

    Args:
        df: DataFrame.

    Returns:
        DataFrame с отфильтрованными устройствами.
    """

    df_warranty = df[
        (df['warranty_expired'] == False) |
        (df['warranty_until_parsed'].isna())
    ].copy()

    return df_warranty

def analyze_clinics(df: pd.DataFrame) -> pd.DataFrame:
    """Анализ проблем по клиникам.

    Args:
        df: DataFrame.

    Returns:
        DataFrame с топ-10 клиник, отсортированных по индексу проблемности.
    """

    clinic_problems = df.groupby(['clinic_id', 'clinic_name', 'city']).agg({
        'device_id': 'count',
        'issues_reported_12mo': 'sum',
        'failure_count_12mo': 'sum',
        'uptime_pct': 'mean',
        'status_normalized': lambda x: (x == 'faulty').sum()
    }).rename(columns={
        'device_id': 'total_device',
        'issues_reported_12mo': 'total_issues',
        'failure_count_12mo': 'total_failures',
        'uptime_pct': 'avg_uptime_pct',
        'status_normalized': 'faulty_count',
    }).reset_index()

    clinic_problems['problem_score'] = (
        clinic_problems['total_issues'] * 1 +
        clinic_problems['total_failures'] * 2 +
        clinic_problems['faulty_count'] * 3 +
        (100 - clinic_problems['avg_uptime_pct']) * 0.5
    )
    clinic_problems = clinic_problems.sort_values('problem_score', ascending=False)
    top_clinics = clinic_problems.head(10)
    
    return top_clinics

def generate_calibration_report(df: pd.DataFrame) -> tuple:
    """Генерация отчёта по калибровке.

    Args:
        df: DataFrame.

    Returns:
        Кортеж из двух DataFrame:
        - calibration_report;
        - overdue_devices.
    """
    df = df.copy()
    df['next_calibration'] = df['last_calibration_date_parsed'] + pd.DateOffset(months=12)
    today = pd.Timestamp(datetime.now().date())

    def calib_status(row):
        if pd.isna(row['last_calibration_date_parsed']):
            return 'no_record'
        elif pd.isna(row['next_calibration']):
            return 'unknown'
        elif row['next_calibration'] < today:
            return 'overdue'
        elif row['next_calibration'] < today + pd.Timedelta(days=30):
            return 'due_soon'
        return 'ok'

    df['calibration_status'] = df.apply(calib_status, axis=1)
    calibration_report = df[
        df['status_normalized'].isin(['operational', 'maintenance_scheduled'])
    ][[
        'device_id', 'clinic_name', 'model', 'last_calibration_date_parsed',
    'next_calibration', 'calibration_status'
    ]]
    overdue_devices = calibration_report[
        calibration_report['calibration_status'] == 'overdue'
    ]

    return calibration_report, overdue_devices

def create_pivot_table(df: pd.DataFrame) -> tuple:
    """Создание сводных таблиц.

    Args:
        df: DataFrame.

    Returns:
        Кортеж из четырёх DataFrame:
        - pivot_clinic;
        - pivot_model;
        - device_table;
        - pivot_matrix.
    """
    
    pivot_clinic =  df.groupby(['clinic_id', 'clinic_name', 'city']).agg({
        'device_id': 'count',
        'issues_reported_12mo': 'sum',
        'failure_count_12mo': 'sum',
        'uptime_pct': 'mean',
        'model': 'nunique'
    }).reset_index()

    pivot_model = df.groupby(['model']).agg({
        'device_id': 'count',
        'clinic_id': 'nunique',
        'issues_reported_12mo': 'sum',
        'failure_count_12mo': 'sum',
        'uptime_pct': 'mean',
        'warranty_expired': 'sum',
    }).reset_index()

    device_table = df[[
        'device_id', 'clinic_id', 'clinic_name', 'city', 'department',
        'model', 'serial_number', 'install_date_parsed', 'status_normalized',
        'warranty_until_parsed', 'last_calibration_date_parsed',
        'last_service_date_parsed', 'issues_reported_12mo',
        'failure_count_12mo', 'uptime_pct', 'issues_text'
    ]]

    pivot_matrix = pd.pivot_table(
        df,
        values = 'device_id',
        index = ['clinic_name', 'city'],
        columns = ['model'],
        aggfunc = 'count',
        fill_value = 0,
        margins = True
    )

    return pivot_clinic, pivot_model, device_table, pivot_matrix


def df_to_devices(df: pd.DataFrame) -> List[MedicalDevice]:
    """Преобразование DataFrame в список объектов MedicalDevice.

    Args:
        df: DataFrame.

    Returns:
        Список объектов MedicalDevice.
    """

    devices = []

    for idx, row in df.iterrows():
        device = MedicalDevice(
            device_id=str(row.get('device_id', '')),
            clinic_id=str(row.get('clinic_id', '')),
            clinic_name=str(row.get('clinic_name', '')),
            city=str(row.get('city', '')),
            department=str(row.get('department', '')),
            model=str(row.get('model', '')),
            serial_number=str(row.get('serial_number', '')),
            install_date=pd.to_datetime(row.get('install_date'), errors='coerce', dayfirst=True),
            warranty_until=pd.to_datetime(row.get('warranty_until'), errors='coerce', dayfirst=True),
            last_calibration_date=pd.to_datetime(row.get('last_calibration_date'), errors='coerce', dayfirst=True),
            last_service_date=pd.to_datetime(row.get('last_service_date'), errors='coerce', dayfirst=True),
            status=str(row.get('status', 'unknown')),
            status_normalized=str(row.get('status_normalized', 'unknown')),
            issues_reported_12mo=int(row.get('issues_reported_12mo', 0) or 0),
            failure_count_12mo=int(row.get('failure_count_12mo', 0) or 0),
            uptime_pct=float(row.get('uptime_pct', 100.0) or 100.0),
            issues_text=str(row.get('issues_text', '')) if pd.notna(row.get('issues_text')) else None
        )
        devices.append(device)

    print(f"Создано объектов MedicalDevice: {len(devices)}")

    return devices

def export_to_excel(data_dict: dict, filepath: str):
    """Экспорт всех результатов в Excel

     Args:
        data_dict;
        filepath.
    """

    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        for sheet_name, df in data_dict.items():
            if isinstance(df, pd.DataFrame):
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                df.to_excel(writer, sheet_name=sheet_name)
                
    print(f"Сохранено в {filepath}")

def run_analysis(excel_path: str) -> dict:
    """Главная функция анализа.

    Args:
        excel_path.

    Returns:
        Словарь с результатами анализа.
    """

    df = load_data(excel_path)
    df = normalize_status(df)
    df = process_data(df)
    df_warranty = filter_by_warranty(df)
    top_clinics = analyze_clinics(df)
    calibration_report, overdue_devices = generate_calibration_report(df)
    pivot_clinic, pivot_model, device_table, pivot_matrix = create_pivot_table(df)

    export_to_excel({
        'raw_data': df,
        'top_clinics': top_clinics,
        'calibration_report': calibration_report,
        'overdue_devices': overdue_devices,
        'by_clinic': pivot_clinic,
        'by_model': pivot_model,
        'device_details': device_table,
        'clinic_model_matrix': pivot_matrix
    }, 'medical_devices_report.xlsx')

    print("Статистика")
    print(f"Всего устройств: {len(df)}")
    print(f"Клиник: {df['clinic_id'].nunique()}")
    print(f"Устройств на гарантии: {len(df_warranty)}")
    print(f"Просроченная калибровка: {len(overdue_devices)}")
    print("\nТоп-5 проблемных клиник:")
    print(top_clinics[['clinic_name', 'city', 'problem_score']].head())

    return {
        'processed_df': df,
        'warranty_df': df_warranty,
        'top_clinics': top_clinics,
        'calibration_report': calibration_report,
        'overdue_devices': overdue_devices,
        'pivot_clinic': pivot_clinic,
        'pivot_model': pivot_model,
        'device_table': device_table,
        'pivot_matrix': pivot_matrix
    }

if __name__ == '__main__':
    results = run_analysis('medical_diagnostic_devices_10000.xlsx')

