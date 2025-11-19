# Havital Firestore Database 結構完整文檔

> **目的**: 為後端管理介面開發提供完整的 Firestore 資料庫架構說明
>
> **最後更新**: 2025-11-19
>
> **版本**: 1.0

---

## 📋 目錄

1. [資料庫概覽](#資料庫概覽)
2. [用戶相關 Collections](#用戶相關-collections)
3. [訓練計畫 Collections](#訓練計畫-collections)
4. [系統功能 Collections](#系統功能-collections)
5. [索引建議](#索引建議)
6. [CRUD 操作指南](#crud-操作指南)
7. [最佳實踐](#最佳實踐)

---

## 資料庫概覽

### 架構設計

Havital 使用 Firebase Firestore 採用**混合型結構**：

```
Firestore
├── users (頂層 Collection)
│   └── {uid} (Document)
│       ├── workouts_v2 (Sub-collection) ⭐ 新版訓練數據
│       ├── workouts_v2_index (Sub-collection) ⭐ 訓練索引
│       ├── health_daily (Sub-collection)
│       ├── targets (Sub-collection)
│       ├── plan_modifications (Sub-collection)
│       ├── weekly_overview (Sub-collection)
│       ├── agent_context (Sub-collection)
│       ├── processing_results (Sub-collection)
│       ├── processing_errors (Sub-collection)
│       └── provider_connections (Sub-collection)
│
├── plan_race_run_overview (頂層 Collection) ⭐ 訓練計畫總覽
├── plan_race_run_weekly (頂層 Collection) ⭐ 週訓練計畫
├── training_readiness_cache (頂層 Collection)
├── weekly_summary (頂層 Collection)
├── provider_activities (頂層 Collection)
├── audit_logs (頂層 Collection)
└── backfill (頂層 Collection)
    ├── strava/items (Sub-collection)
    └── garmin/items (Sub-collection)
```

### 設計原則

- **用戶隔離**: 用戶專屬數據存於 `users/{uid}/` 下的子集合
- **全局資源**: 訓練計畫、快取等存於頂層 Collections
- **時區標準**: 所有時間戳均使用 UTC 儲存
- **版本管理**: workouts_v2 為新版，workouts (舊版) 僅供兼容

---

## 用戶相關 Collections

### 1. users (頂層 Collection)

**Collection Path**: `users`
**Document ID**: Firebase UID (例: `abc123xyz`)

#### 文檔結構

```typescript
{
  // === 基本資訊 ===
  uid: string,                    // Firebase UID
  email: string,                  // 用戶 email
  display_name?: string,          // 顯示名稱
  photo_url?: string,             // 頭像 URL
  created_at: Timestamp,          // 註冊時間
  updated_at: Timestamp,          // 最後更新時間

  // === 用戶設定 ===
  language?: string,              // zh-TW, en-US, ja-JP
  timezone?: string,              // Asia/Taipei, America/New_York

  // === 訓練相關 ===
  active_training_id?: string,    // 當前活躍的訓練計畫 ID
  vdot?: number,                  // 當前 VDOT 值 (例: 45.5)
  max_hr?: number,                // 最大心率 (bpm)
  resting_hr?: number,            // 靜息心率 (bpm)

  // === Provider 連接 ===
  strava_user_id?: string,        // Strava 用戶 ID
  garmin_user_id?: string,        // Garmin 用戶 ID
  apple_health_enabled?: boolean, // Apple Health 是否啟用

  // === 訂閱狀態 ===
  subscription_status?: string,   // active, inactive, trial
  subscription_tier?: string      // free, premium, pro
}
```

#### Repository

**位置**: `core/database/repositories/user_repository.py`

**主要方法**:

```python
# 獲取用戶資料
user_data = user_repository.get_user(uid)

# 更新用戶資料
user_repository.update_user(uid, {
    'display_name': '新名稱',
    'timezone': 'Asia/Tokyo'
})

# 通過 Provider ID 查找用戶
user = user_repository.get_user_by_provider_id('strava', 'strava_user_123')

# 更新活躍訓練計畫
user_repository.update_active_training_id(uid, 'training_plan_xyz')
```

#### 常用查詢

```python
# 查詢所有用戶
users = db.collection('users').stream()

# 查詢特定語言的用戶
users = db.collection('users').where('language', '==', 'zh-TW').stream()

# 查詢有活躍訓練計畫的用戶
users = db.collection('users').where('active_training_id', '!=', None).stream()
```

---

### 2. users/{uid}/workouts_v2 ⭐ 新版訓練數據

**Collection Path**: `users/{uid}/workouts_v2/providers/{provider}/{activity_id}`
**Document ID**: Provider 活動 ID (例: Strava 的 `12345678`)

#### 路徑結構

```
users/{uid}/workouts_v2/
  └── providers/ (Document)
      ├── strava/ (Sub-collection)
      │   ├── 12345678 (Document)
      │   └── 87654321 (Document)
      ├── garmin/ (Sub-collection)
      │   └── 98765432 (Document)
      └── apple_health/ (Sub-collection)
          └── ... (Document)
```

#### 文檔結構

```typescript
{
  // === 基本資訊 ===
  activity_id: string,              // Provider 的活動 ID
  provider: string,                 // strava, garmin, apple_health
  activity_type: string,            // running, cycling, swimming, walking, etc.
  training_type?: string,           // recovery_run, easy_run, tempo, interval, long_run, etc.

  // === 時間資訊 (全部 UTC) ===
  start_time_utc: Timestamp,        // 開始時間 (UTC)
  end_time_utc: Timestamp,          // 結束時間 (UTC)
  duration_s: number,               // 總時長 (秒)

  // === 基本指標 ===
  distance_m: number,               // 距離 (公尺)
  avg_heart_rate_bpm?: number,      // 平均心率
  max_heart_rate_bpm?: number,      // 最大心率
  avg_speed_m_per_s?: number,       // 平均速度 (m/s)
  avg_pace_s_per_km?: number,       // 平均配速 (秒/公里)

  // === 進階指標 ===
  total_ascent_m?: number,          // 總爬升 (公尺)
  total_descent_m?: number,         // 總下降 (公尺)
  calories?: number,                // 消耗卡路里

  // === Advanced Metrics (Havital 獨家算法) ===
  advanced_metrics?: {
    tss?: number,                   // Training Stress Score
    if?: number,                    // Intensity Factor
    np?: number,                    // Normalized Power
    aerobic_te?: number,            // 有氧訓練效果
    anaerobic_te?: number,          // 無氧訓練效果
    hrv_stress?: number,            // HRV 壓力
    performance_condition?: number  // 表現狀況
  },

  // === Lap 數據 ===
  laps?: Array<{
    lap_number: number,             // 圈數 (1, 2, 3...)
    start_time_offset_s: number,    // 相對開始時間偏移 (秒)
    total_time_s: number,           // 該圈總時長 (秒)
    total_distance_m: number,       // 該圈距離 (公尺)
    avg_pace_s_per_km?: number,     // 平均配速
    avg_heart_rate_bpm?: number,    // 平均心率
    max_heart_rate_bpm?: number,    // 最大心率
    avg_cadence?: number,           // 平均步頻
    total_ascent_m?: number,        // 爬升
    total_descent_m?: number        // 下降
  }>,

  // === 原始數據 ===
  fit_file_url?: string,            // FIT 檔案 URL (Google Cloud Storage)
  gpx_file_url?: string,            // GPX 檔案 URL
  tcx_file_url?: string,            // TCX 檔案 URL

  // === 處理狀態 ===
  processing_status?: string,       // pending, processing, completed, failed
  error_message?: string,           // 錯誤訊息 (如果失敗)
  processing_attempts?: number,     // 處理嘗試次數

  // === 時間戳 ===
  created_at: Timestamp,            // 創建時間
  updated_at: Timestamp             // 最後更新時間
}
```

#### Data Models

**位置**: `data_models/workout_v2.py`

```python
from data_models.workout_v2 import (
    WorkoutV2Model,        # 完整訓練數據模型
    LapData,               # 圈速數據模型
    AdvancedMetrics,       # 進階指標模型
    ActivityType           # 運動類型枚舉
)

# 支援的運動類型 (30+ 種)
ActivityType.RUNNING
ActivityType.CYCLING
ActivityType.SWIMMING
ActivityType.WALKING
ActivityType.HIKING
# ... 更多類型
```

#### Repository

**位置**: `core/database/repositories/workout_repository.py`

**主要方法**:

```python
# 獲取特定 Provider 的訓練
workout = workout_repository.get_workout_by_provider_id(
    uid='user123',
    provider='strava',
    activity_id='12345678'
)

# 儲存 V2 訓練數據
workout_repository.save_workout_v2(
    uid='user123',
    provider='strava',
    activity_id='12345678',
    data={
        'activity_type': 'running',
        'start_time_utc': datetime.now(timezone.utc),
        'distance_m': 5000,
        # ... 其他欄位
    }
)

# 查詢日期範圍內的訓練
workouts = workout_repository.query_workouts_by_date_range(
    uid='user123',
    start_date='2024-03-01',
    end_date='2024-03-31'
)

# 刪除訓練數據
workout_repository.delete_workout_v2(
    uid='user123',
    provider='strava',
    activity_id='12345678'
)
```

#### 常用查詢

```python
# 查詢用戶所有 Strava 訓練
strava_workouts = (db.collection('users')
                     .document(uid)
                     .collection('workouts_v2')
                     .document('providers')
                     .collection('strava')
                     .stream())

# 查詢特定活動
workout_ref = (db.collection('users')
                 .document(uid)
                 .collection('workouts_v2')
                 .document('providers')
                 .collection('strava')
                 .document('12345678'))

workout = workout_ref.get()
```

#### 重要注意事項

⚠️ **V2 架構特性**:
- Provider 分離儲存，避免 ID 衝突
- 路徑包含 `providers/` 中間層
- 支援多 Provider 同時存在

⚠️ **時區處理**:
- 所有時間欄位 (`start_time_utc`, `end_time_utc`) 必須是 UTC
- 顯示時需使用 `timezone_utils` 轉換到用戶時區

⚠️ **與舊版差異**:
- 舊版: `users/{uid}/workouts/{activity_id}`
- 新版: `users/{uid}/workouts_v2/providers/{provider}/{activity_id}`
- 建議所有新功能使用 V2

---

### 3. users/{uid}/workouts_v2_index ⭐ 訓練索引

**Collection Path**: `users/{uid}/workouts_v2_index`
**Document ID**: `{YYYY-MM-DD}_{provider}_{activity_id}` (例: `2024-03-15_strava_12345678`)

#### 用途

- **快速查詢**: 無需讀取完整訓練數據即可顯示列表
- **日期過濾**: 支援按日期範圍快速查詢
- **計畫匹配**: 記錄訓練與計畫的對應關係

#### 文檔結構

```typescript
{
  // === 關聯資訊 ===
  workout_doc_path: string,         // 完整路徑: users/{uid}/workouts_v2/providers/{provider}/{activity_id}
  activity_id: string,              // Provider 活動 ID
  provider: string,                 // strava, garmin, apple_health

  // === 基本摘要 (用於列表顯示) ===
  activity_type: string,            // running, cycling, etc.
  training_type?: string,           // recovery_run, tempo, etc.
  start_time_utc: Timestamp,        // 開始時間 (UTC)
  duration_s: number,               // 時長 (秒)
  distance_m: number,               // 距離 (公尺)

  // === 關鍵指標 (快速過濾用) ===
  avg_pace_s_per_km?: number,       // 平均配速
  avg_heart_rate_bpm?: number,      // 平均心率
  tss?: number,                     // Training Stress Score

  // === 計畫匹配 ===
  matched_plan_id?: string,         // 對應的訓練計畫 overview_id
  matched_week?: number,            // 對應的訓練週次
  matched_day_index?: number,       // 對應的訓練日 (1-7)

  // === 時間戳 ===
  indexed_at: Timestamp             // 索引建立時間
}
```

#### Repository

**位置**: `core/database/repositories/workout_repository.py`

**主要方法**:

```python
# 創建索引
workout_repository.create_workout_index(
    uid='user123',
    workout_data={
        'activity_id': '12345678',
        'provider': 'strava',
        'start_time_utc': datetime.now(timezone.utc),
        # ... 其他欄位
    }
)

# 查詢特定日期的訓練索引
indexes = workout_repository.query_workouts_index_by_date(
    uid='user123',
    date='2024-03-15'
)

# 刪除索引
workout_repository.delete_workout_index(
    uid='user123',
    index_id='2024-03-15_strava_12345678'
)
```

#### 常用查詢

```python
# 查詢特定週的訓練索引
week_start = datetime(2024, 3, 11, tzinfo=timezone.utc)
week_end = datetime(2024, 3, 18, tzinfo=timezone.utc)

indexes = (db.collection('users')
             .document(uid)
             .collection('workouts_v2_index')
             .where('start_time_utc', '>=', week_start)
             .where('start_time_utc', '<', week_end)
             .order_by('start_time_utc')
             .stream())

# 查詢特定計畫的所有匹配訓練
matched_workouts = (db.collection('users')
                      .document(uid)
                      .collection('workouts_v2_index')
                      .where('matched_plan_id', '==', 'plan_xyz')
                      .stream())
```

#### 索引建議

```
複合索引:
- start_time_utc (ASC) + provider (ASC)
- start_time_utc (DESC) + activity_type (ASC)
- matched_plan_id (ASC) + matched_day_index (ASC)
```

---

### 4. users/{uid}/health_daily

**Collection Path**: `users/{uid}/health_daily`
**Document ID**: `YYYY-MM-DD` (例: `2024-03-15`)

#### 文檔結構

```typescript
{
  // === 基本資訊 ===
  date: string,                     // YYYY-MM-DD
  user_id: string,                  // Firebase UID

  // === 心率數據 ===
  resting_heart_rate?: number,      // 靜息心率 (bpm)
  avg_heart_rate?: number,          // 平均心率 (bpm)
  max_heart_rate?: number,          // 最大心率 (bpm)

  // === HRV (心率變異性) ===
  hrv_last_night_avg?: number,      // 昨晚平均 HRV (ms)
  hrv_last_night_5min_high?: number,// 昨晚 5 分鐘最高 HRV (ms)

  // === 步數和活動 ===
  daily_steps?: number,             // 每日步數
  daily_distance_m?: number,        // 每日距離 (公尺)
  daily_calories?: number,          // 每日消耗卡路里
  floors_climbed?: number,          // 爬樓層數
  active_minutes?: number,          // 活動分鐘數

  // === 睡眠數據 ===
  sleep_data?: {
    total_sleep_minutes?: number,   // 總睡眠時間 (分鐘)
    deep_sleep_minutes?: number,    // 深層睡眠 (分鐘)
    rem_sleep_minutes?: number,     // REM 睡眠 (分鐘)
    light_sleep_minutes?: number,   // 淺層睡眠 (分鐘)
    awake_minutes?: number,         // 清醒時間 (分鐘)
    sleep_efficiency_percent?: number, // 睡眠效率 (%)
    bedtime?: string,               // 就寢時間 (ISO 8601)
    wake_time?: string              // 起床時間 (ISO 8601)
  },

  // === 身體組成 ===
  body_weight_kg?: number,          // 體重 (公斤)
  body_fat_percent?: number,        // 體脂率 (%)
  muscle_mass_kg?: number,          // 肌肉量 (公斤)
  bone_mass_kg?: number,            // 骨量 (公斤)
  water_percent?: number,           // 水分 (%)

  // === 血壓 ===
  systolic_bp?: number,             // 收縮壓
  diastolic_bp?: number,            // 舒張壓

  // === 血糖 ===
  blood_glucose_mg_dl?: number,     // 血糖 (mg/dL)

  // === 壓力和環境 ===
  stress_level?: number,            // 壓力等級 (0-100)
  ambient_temperature_c?: number,   // 環境溫度 (°C)
  humidity_percent?: number,        // 濕度 (%)

  // === 數據來源 ===
  data_sources?: string[],          // ['garmin', 'apple_health']

  // === 數據完整性標記 ===
  has_heart_rate_data: boolean,
  has_steps_data: boolean,
  has_sleep_data: boolean,
  has_hrv_data: boolean,

  // === 時間戳 ===
  created_at: Timestamp,
  updated_at: Timestamp
}
```

#### Data Models

**位置**: `data_models/daily_health.py`

```python
from data_models.daily_health import (
    DailyHealthModel,         # 每日健康數據模型
    SleepData,                # 睡眠數據模型
    StepsData,                # 步數數據模型
    HeartRateData,            # 心率數據模型
    DailyHealthMetrics        # 完整健康指標模型
)
```

#### Repository

**位置**: `core/database/repositories/health_repository.py`

**主要方法**:

```python
# 獲取特定日期的健康數據
health_data = health_repository.get_health_data(
    uid='user123',
    date='2024-03-15'
)

# 儲存健康數據
health_repository.save_health_data(
    uid='user123',
    date='2024-03-15',
    data={
        'resting_heart_rate': 58,
        'daily_steps': 10000,
        'sleep_data': {
            'total_sleep_minutes': 480,
            'deep_sleep_minutes': 120
        }
    }
)

# 查詢日期範圍的健康數據
health_data_list = health_repository.query_health_data_range(
    uid='user123',
    start_date='2024-03-01',
    end_date='2024-03-31'
)
```

#### 常用查詢

```python
# 查詢過去 7 天的健康數據
from datetime import datetime, timedelta, timezone

end_date = datetime.now(timezone.utc)
start_date = end_date - timedelta(days=7)

health_docs = (db.collection('users')
                 .document(uid)
                 .collection('health_daily')
                 .where('date', '>=', start_date.strftime('%Y-%m-%d'))
                 .where('date', '<=', end_date.strftime('%Y-%m-%d'))
                 .order_by('date', direction=firestore.Query.DESCENDING)
                 .stream())
```

---

### 5. users/{uid}/targets

**Collection Path**: `users/{uid}/targets`
**Document ID**: 自動生成或自訂 (例: `race_2024_marathon`)

#### 文檔結構

```typescript
{
  // === 基本資訊 ===
  id?: string,                      // 目標 ID
  name: string,                     // 目標名稱 (例: "2024 台北馬拉松")
  type: string,                     // run, race_run, cycling

  // === 通用屬性 ===
  distance_km?: number,             // 距離 (公里)
  training_weeks?: number,          // 訓練週數

  // === 賽事特有屬性 (type = race_run) ===
  race_date?: number,               // 賽事日期 (UTC timestamp)
  is_main_race?: boolean,           // 是否為主要賽事
  target_pace?: string,             // 目標配速 (MM:SS 格式, 例: "05:30")
  target_time?: number,             // 目標完賽時間 (秒)

  // === 自行車特有屬性 (type = cycling) ===
  elevation_gain_m?: number,        // 爬升 (公尺)

  // === 時間戳 ===
  created_at: Timestamp,
  updated_at: Timestamp
}
```

#### Data Models

**位置**: `data_models/target.py`

```python
from data_models.target import (
    TargetModel,          # 統一的目標模型
    RaceRunTarget,        # 賽事目標
    RunTarget,            # 一般跑步目標
    CyclingTarget,        # 自行車目標
    TargetType            # 目標類型枚舉
)

# 目標類型
TargetType.RUN          # 一般跑步目標
TargetType.RACE_RUN     # 賽事目標
TargetType.CYCLING      # 自行車目標
```

#### Repository

**位置**: `core/database/repositories/target_repository.py`

**主要方法**:

```python
# 獲取目標
target = target_repository.get_target(
    uid='user123',
    target_id='race_2024_marathon'
)

# 創建目標
target_id = target_repository.create_target(
    uid='user123',
    target_data={
        'name': '2024 台北馬拉松',
        'type': 'race_run',
        'distance_km': 42.195,
        'race_date': 1704067200,  # UTC timestamp
        'target_pace': '05:30',
        'is_main_race': True
    }
)

# 更新目標
target_repository.update_target(
    uid='user123',
    target_id='race_2024_marathon',
    updates={'target_pace': '05:15'}
)

# 獲取主要賽事
main_race = target_repository.get_main_race(uid='user123')

# 列出所有目標
targets = target_repository.list_targets(uid='user123')
```

---

### 6. users/{uid}/plan_modifications

**Collection Path**: `users/{uid}/plan_modifications`
**Document ID**: 自動生成的修改 ID

#### 文檔結構

```typescript
{
  modification_id: string,          // 修改 ID
  overview_id: string,              // 對應的訓練計畫概覽 ID
  week_of_plan: number,             // 第幾週
  modification_type: string,        // adjust_distance, skip_workout, etc.

  // === 修改詳情 ===
  original_data?: object,           // 原始數據
  modified_data?: object,           // 修改後的數據
  reason?: string,                  // 修改原因

  // === 時間戳 ===
  created_at: Timestamp,
  applied_at?: Timestamp            // 應用修改的時間
}
```

#### 使用位置

直接在 `domains/training_plan/training_service.py` 中操作，無專用 repository。

---

### 7. users/{uid}/weekly_overview

**Collection Path**: `users/{uid}/weekly_overview`
**Document ID**: `{year}_W{week_number}` (例: `2024_W12`)

#### 文檔結構

```typescript
{
  // === 基本資訊 ===
  year: number,                     // 年份 (2024)
  week_number: number,              // 週次 (1-52)
  week_start_date: string,          // 週開始日期 (YYYY-MM-DD)
  week_end_date: string,            // 週結束日期 (YYYY-MM-DD)

  // === TSS 數據 ===
  total_tss: number,                // 當週總 TSS
  ctl: number,                      // Chronic Training Load (慢性訓練負荷)
  atl: number,                      // Acute Training Load (急性訓練負荷)
  tsb: number,                      // Training Stress Balance (訓練壓力平衡)

  // === 訓練摘要 ===
  total_distance_km: number,        // 總距離 (公里)
  total_workouts: number,           // 總訓練次數
  total_duration_s: number,         // 總時長 (秒)

  // === 時間戳 ===
  created_at: Timestamp,
  updated_at: Timestamp
}
```

#### 使用位置

在 `domains/training_plan/services/tss_trends_service.py` 中操作。

---

### 8. users/{uid}/agent_context

**Collection Path**: `users/{uid}/agent_context`
**Document ID**: `pending_modification`

#### 文檔結構

```typescript
{
  modification_request: string,     // AI Agent 待處理的修改請求
  context_data: object,             // 上下文數據
  status: string,                   // pending, processing, completed

  created_at: Timestamp,
  updated_at: Timestamp
}
```

#### Repository

**位置**: `domains/rizo/storage/modification_storage.py`

---

### 9. users/{uid}/processing_results

**Collection Path**: `users/{uid}/processing_results`
**Document ID**: 自動生成

#### 文檔結構

```typescript
{
  provider: string,                 // strava, garmin, apple_health
  activity_id: string,              // 活動 ID
  processing_status: string,        // completed
  result_data: object,              // 處理結果數據

  created_at: Timestamp
}
```

---

### 10. users/{uid}/processing_errors

**Collection Path**: `users/{uid}/processing_errors`
**Document ID**: 自動生成

#### 文檔結構

```typescript
{
  provider: string,                 // strava, garmin, apple_health
  activity_id: string,              // 活動 ID
  error_type: string,               // validation_error, api_error, etc.
  error_message: string,            // 錯誤訊息
  stack_trace?: string,             // 堆疊追蹤

  created_at: Timestamp
}
```

---

### 11. users/{uid}/provider_connections

**Collection Path**: `users/{uid}/provider_connections`
**Document ID**: Provider 名稱 (`strava`, `garmin`, `apple_health`)

#### 文檔結構

```typescript
{
  provider: string,                 // strava, garmin, apple_health
  connected: boolean,               // 是否已連接
  provider_user_id?: string,        // Provider 端的用戶 ID

  // === 認證資訊 (加密) ===
  access_token?: string,            // 存取 Token (加密)
  refresh_token?: string,           // 刷新 Token (加密)
  expires_at?: Timestamp,           // Token 過期時間

  // === 同步狀態 ===
  last_sync_at?: Timestamp,         // 最後同步時間

  // === 時間戳 ===
  created_at: Timestamp,
  updated_at: Timestamp
}
```

#### 安全注意

⚠️ **敏感數據加密**: `access_token` 和 `refresh_token` 必須使用加密儲存。
詳見: `core/encryption/encryption_service.py`

---

## 訓練計畫 Collections

### 12. plan_race_run_overview ⭐ 訓練計畫概覽

**Collection Path**: `plan_race_run_overview`
**Document ID**: 自動生成或 `training_{uid}` 格式

#### 文檔結構

```typescript
{
  // === 基本資訊 ===
  id?: string,                      // 計畫 ID
  uid: string,                      // Firebase UID
  main_race_id?: string,            // 主要賽事 ID

  // === 計畫概覽 ===
  training_plan_name: string,       // 訓練計畫名稱
  target_evaluate: string,          // 對目標的評估
  total_weeks: number,              // 總週數
  training_hightlight: string,      // 訓練亮點 (注意: 保留原始拼寫)

  // === 訓練階段 ===
  training_stage_discription: Array<{  // 注意: 保留原始拼寫
    stage_name: string,             // 階段名稱 (例: "基礎期")
    stage_id: string,               // base, build, peak, taper
    stage_description: string,      // 階段描述
    training_focus: string,         // 訓練重點
    week_start: number,             // 開始週次 (1, 5, 9...)
    week_end?: number,              // 結束週次
    target_distance_km_low: number, // 目標跑量下限 (公里)
    target_distance_km_hight: number,  // 目標跑量上限 (公里) - 保留原始拼寫
    target_pace: string,            // 目標配速 (MM:SS)
    post_race_recovery?: boolean    // 是否為賽後恢復期
  }>,

  // === 賽事歷史 (多賽事支援) ===
  race_history?: Array<{
    race_id: string,                // 賽事 ID
    race_name: string,              // 賽事名稱
    distance_km: number,            // 距離
    target_pace: string,            // 目標配速
    completed_date: string,         // 完賽日期 (YYYY-MM-DD)
    week_range: number[],           // 週次範圍 [start, end]
    training_summary?: {
      total_workouts: number,
      total_distance_km: number,
      final_vdot?: number,
      completion_rate: number,
      training_period_days: number
    }
  }>,

  // === 延展資訊 (多賽事延展) ===
  extension_info?: {
    is_extended: boolean,           // 是否已延展
    original_total_weeks: number,   // 原始總週數
    extensions: Array<{
      extended_at: string,          // 延展時間 (ISO 8601)
      from_race_id: string,         // 從哪個賽事延展
      to_race_id: string,           // 延展到哪個賽事
      additional_weeks: number,     // 增加的週數
      days_between_races: number,   // 賽事間隔天數
      extension_reason: string,     // 延展原因
      recovery_strategy: string     // 恢復策略
    }>
  },

  // === 時間戳 ===
  created_at: Timestamp,
  updated_at: Timestamp
}
```

#### Data Models

**位置**: `data_models/plan_models.py`

```python
from data_models.plan_models import (
    PlanRunOverviewModel,     # 訓練計畫概覽模型
    TrainingStageModel,       # 訓練階段模型
    RaceHistory,              # 賽事歷史模型
    ExtensionInfo             # 延展資訊模型
)
```

#### Repository

**位置**: `core/database/repositories/training_plan_repository.py`

**主要方法**:

```python
# 獲取計畫概覽
overview = training_plan_repository.get_plan_overview(overview_id='plan_xyz')

# 創建計畫概覽
overview_id = training_plan_repository.create_plan_overview(
    uid='user123',
    overview_data={
        'training_plan_name': '2024 全馬訓練計畫',
        'total_weeks': 16,
        'training_stage_discription': [
            {
                'stage_id': 'base',
                'stage_name': '基礎期',
                'week_start': 1,
                'week_end': 4,
                'target_distance_km_low': 30,
                'target_distance_km_hight': 40
            }
            # ... 更多階段
        ]
    }
)

# 更新計畫概覽
training_plan_repository.update_plan_overview(
    overview_id='plan_xyz',
    updates={'total_weeks': 18}
)

# 獲取用戶當前活躍的計畫
active_plan = training_plan_repository.get_active_plan_overview(uid='user123')
```

#### 常用查詢

```python
# 查詢用戶的所有訓練計畫
overviews = (db.collection('plan_race_run_overview')
               .where('uid', '==', uid)
               .order_by('created_at', direction=firestore.Query.DESCENDING)
               .stream())

# 查詢特定賽事的訓練計畫
plans = (db.collection('plan_race_run_overview')
           .where('main_race_id', '==', 'race_2024_marathon')
           .stream())
```

---

### 13. plan_race_run_weekly ⭐ 週訓練計畫

**Collection Path**: `plan_race_run_weekly`
**Document ID**: `{overview_id}_week_{week_number}` 或自動生成

#### 文檔結構

```typescript
{
  // === 關聯資訊 ===
  uid: string,                      // Firebase UID
  overview_id: string,              // 對應的訓練計畫概覽 ID
  week_of_plan: number,             // 第幾週 (1-N)
  total_weeks: number,              // 總週數

  // === 週計畫概覽 ===
  purpose: string,                  // 當週訓練目的
  total_distance_km: number,        // 總距離 (公里)
  total_distance_reason: string,    // 跑量決定原因
  design_reason: string[],          // 安排理由列表

  // === 強度分鐘數分布 ===
  intensity_total_minutes?: {
    low: number,                    // 低強度分鐘數
    medium: number,                 // 中強度分鐘數
    high: number                    // 高強度分鐘數
  },

  // === 每日訓練詳情 ===
  days: Array<{
    day_index: number,              // 1-7 (星期一到星期日)
    training_type: string,          // recovery_run, easy_run, tempo, interval, rest, etc.
    day_target: string,             // 當日訓練目標
    reason: string,                 // 為何安排這樣的課表
    tips?: string,                  // 注意事項

    // === 訓練詳情 (Union Type，根據 training_type 不同) ===
    training_details:
      // 1. 休息日
      | {
          description: string       // "完全休息" 或 "主動恢復"
        }

      // 2. 一般訓練 (recovery_run, easy_run, long_run, tempo 等)
      | {
          distance_km: number,      // 距離 (公里)
          pace?: string,            // 配速 (MM:SS 格式)
          heart_rate_range?: {      // 心率區間
            min: number,            // 最低心率 (bpm)
            max: number             // 最高心率 (bpm)
          },
          description: string       // 訓練描述
        }

      // 3. 間歇訓練 (interval)
      | {
          repeats: number,          // 重複次數 (例: 8 次)
          work: {                   // 工作段
            distance_km?: number,   // 距離 (公里)
            distance_m?: number,    // 距離 (公尺)
            time_minutes?: number,  // 時間 (分鐘)
            pace: string,           // 配速 (MM:SS)
            description: string     // 描述 (例: "1000m 間歇")
          },
          recovery: {               // 恢復段
            distance_km?: number,   // null 表示靜止休息
            distance_m?: number,
            time_minutes?: number,
            pace?: string,          // null 表示走路或靜止
            description: string     // 描述 (例: "400m 慢跑恢復")
          }
        }

      // 4. 組合訓練/漸速跑 (progression_run, fartlek, combination)
      | {
          segments: Array<{         // 訓練段落
            distance_km: number,
            pace: string,
            description: string,
            heart_rate_range?: {
              min: number,
              max: number
            }
          }>,
          total_distance_km: number,
          description: string
        }
  }>,

  // === 時間戳 ===
  created_at: Timestamp,
  updated_at: Timestamp
}
```

#### Data Models

**位置**: `data_models/plan_models.py`

```python
from data_models.plan_models import (
    WeeklyTrainingPlan,       # 週訓練計畫模型
    DayDetail,                # 每日訓練詳情模型
    IntervalTraining,         # 間歇訓練模型
    CombinationTraining,      # 組合訓練模型
    GeneralTraining,          # 一般訓練模型
    RestTraining              # 休息模型
)
```

#### Repository

**位置**: `core/database/repositories/training_plan_repository.py`

**主要方法**:

```python
# 獲取週計畫
weekly_plan = training_plan_repository.get_weekly_plan(plan_id='week_plan_xyz')

# 創建週計畫
plan_id = training_plan_repository.create_weekly_plan(
    uid='user123',
    overview_id='plan_xyz',
    week_number=1,
    plan_data={
        'purpose': '建立有氧基礎',
        'total_distance_km': 35,
        'days': [
            {
                'day_index': 1,
                'training_type': 'rest',
                'day_target': '完全休息',
                'reason': '週一休息恢復',
                'training_details': {
                    'description': '完全休息'
                }
            },
            {
                'day_index': 2,
                'training_type': 'easy_run',
                'day_target': '輕鬆跑 8km',
                'reason': '恢復跑建立基礎',
                'training_details': {
                    'distance_km': 8,
                    'pace': '06:00',
                    'description': '輕鬆跑，心率控制在有氧區間'
                }
            }
            # ... 更多天
        ]
    }
)

# 更新週計畫
training_plan_repository.update_weekly_plan(
    plan_id='week_plan_xyz',
    updates={'total_distance_km': 40}
)

# 獲取當週計畫
current_plan = training_plan_repository.get_current_week_plan(
    uid='user123',
    overview_id='plan_xyz'
)
```

#### 常用查詢

```python
# 查詢特定計畫的所有週
weekly_plans = (db.collection('plan_race_run_weekly')
                  .where('overview_id', '==', overview_id)
                  .order_by('week_of_plan')
                  .stream())

# 查詢特定週
plan = (db.collection('plan_race_run_weekly')
          .where('overview_id', '==', overview_id)
          .where('week_of_plan', '==', week_number)
          .limit(1)
          .get())
```

#### 索引建議

```
複合索引:
- uid (ASC) + overview_id (ASC) + week_of_plan (ASC)
- overview_id (ASC) + week_of_plan (ASC)
```

---

## 系統功能 Collections

### 14. training_readiness_cache

**Collection Path**: `training_readiness_cache`
**Document ID**: `{uid}_{YYYY-MM-DD}` (例: `user123_2024-03-15`)

#### 文檔結構

```typescript
{
  // === 基本資訊 ===
  uid: string,                      // Firebase UID
  date: string,                     // YYYY-MM-DD

  // === 整體狀態 ===
  overall_score?: number,           // 整體準備度分數 (0-100)
  overall_status_text?: string,     // 整體狀態文字 (例: "準備充分")
  last_updated_time?: string,       // 最後更新時間 (HH:MM)

  // === 各項指標 ===
  metrics: {
    // 1. 速度指標
    speed?: {
      score: number,                // 分數 (0-100)
      achievement_rate?: number,    // 達成率 (%)
      status_text?: string,         // 狀態文字
      trend?: string,               // improving, stable, declining, insufficient_data
      trend_data?: {
        values: number[],           // 趨勢數值
        dates?: string[],           // 趨勢日期
        direction?: string          // up, down, stable
      },
      recent_workouts?: object[],   // 近期訓練
      message?: string              // 訊息
    },

    // 2. 耐力指標
    endurance?: {
      score: number,
      long_run_completion?: number, // 長跑完成度 (%)
      volume_consistency?: number,  // 跑量一致性 (%)
      status_text?: string,
      trend?: string,
      trend_data?: object,
      message?: string
    },

    // 3. 比賽適能指標
    race_fitness?: {
      score: number,
      current_vdot?: number,        // 當前 VDOT
      target_vdot?: number,         // 目標 VDOT
      baseline_vdot?: number,       // 基線 VDOT
      estimated_race_time?: string, // 預估完賽時間 (HH:MM:SS)
      target_race_time?: string,    // 目標完賽時間
      time_gap_seconds?: number,    // 時間差距 (秒)
      vdot_gap?: number,            // VDOT 差距
      progress_percentage?: number, // 進度百分比
      training_progress?: number,   // 訓練進度 (%)
      data_completed?: boolean,     // 數據是否完整
      data_completeness?: object,   // 數據完整性詳情
      race_pace_training_quality?: number,  // 比賽配速訓練品質
      time_to_race_days?: number,   // 距離比賽天數
      readiness_level?: string,     // 準備度等級
      status_text?: string,
      trend_data?: object,
      message?: string
    },

    // 4. 訓練負荷指標
    training_load?: {
      score: number,
      current_tsb?: number,         // 當前訓練壓力平衡
      ctl?: number,                 // 慢性訓練負荷
      atl?: number,                 // 急性訓練負荷
      balance_status?: string,      // 平衡狀態
      status_text?: string,
      trend_data?: object,
      message?: string
    },

    // 5. 恢復指標
    recovery?: {
      score: number,
      rest_days_count?: number,     // 休息天數
      recovery_quality?: string,    // 恢復品質
      fatigue_level?: string,       // 疲勞等級
      status_text?: string,
      trend_data?: object,
      message?: string
    }
  },

  // === 數據來源和時間 ===
  data_source: string,              // cache, real_time
  last_updated: string,             // 最後更新 (ISO 8601)

  // === 快取控制 ===
  expires_at: Timestamp,            // 過期時間

  // === 時間戳 ===
  created_at: Timestamp
}
```

#### Data Models

**位置**: `data_models/training_readiness_models.py`

```python
from data_models.training_readiness_models import (
    TrainingReadinessResponse,    # 訓練準備度回應模型
    TrainingReadinessMetrics,     # 指標集合模型
    SpeedMetric,                  # 速度指標模型
    EnduranceMetric,              # 耐力指標模型
    RaceFitnessMetric,            # 比賽適能指標模型
    TrainingLoadMetric,           # 訓練負荷指標模型
    RecoveryMetric,               # 恢復指標模型
    TrendData                     # 趨勢數據模型
)
```

#### Repository

**位置**: `core/database/repositories/training_readiness_repository.py`

**主要方法**:

```python
# 獲取快取的準備度數據
readiness = training_readiness_repository.get_cached_readiness(
    uid='user123',
    date='2024-03-15'
)

# 儲存準備度快取
training_readiness_repository.save_readiness_cache(
    uid='user123',
    date='2024-03-15',
    data={
        'overall_score': 85,
        'metrics': {
            'speed': {'score': 80, 'trend': 'improving'},
            'endurance': {'score': 90, 'trend': 'stable'}
        }
    }
)

# 清除過期快取
training_readiness_repository.clear_expired_cache(uid='user123')
```

#### 索引建議

```
複合索引:
- uid (ASC) + date (DESC)
- uid (ASC) + expires_at (ASC)
```

---

### 15. weekly_summary

**Collection Path**: `weekly_summary`
**Document ID**: `{uid}_{overview_id}_week_{week_number}` 或自動生成

#### 文檔結構

```typescript
{
  // === 關聯資訊 ===
  uid: string,                      // Firebase UID
  overview_id: string,              // 訓練計畫概覽 ID
  week_of_plan: number,             // 第幾週
  weekly_plan_id: string,           // 對應的週計畫 ID

  // === 週摘要 ===
  week_start_date: string,          // 週開始日期 (YYYY-MM-DD)
  week_end_date: string,            // 週結束日期 (YYYY-MM-DD)

  // === 執行統計 ===
  total_planned_workouts: number,   // 計劃訓練次數
  total_completed_workouts: number, // 完成訓練次數
  completion_rate: number,          // 完成率 (0-100)

  planned_distance_km: number,      // 計劃跑量 (公里)
  completed_distance_km: number,    // 完成跑量 (公里)
  distance_achievement_rate: number,// 跑量達成率 (%)

  // === 每日執行狀態 ===
  daily_status: Array<{
    day_index: number,              // 1-7
    date: string,                   // YYYY-MM-DD
    planned: boolean,               // 是否有計劃訓練
    completed: boolean,             // 是否已完成
    matched_workout_id?: string     // 匹配的訓練 ID
  }>,

  // === 時間戳 ===
  created_at: Timestamp,
  updated_at: Timestamp
}
```

#### Repository

**位置**: `core/database/repositories/summary_repository.py`

---

### 16. provider_activities

**Collection Path**: `provider_activities`
**Document ID**: `{provider}_{provider_user_id}_{activity_id}`

#### 文檔結構

```typescript
{
  provider: string,                 // strava, garmin, apple_health
  provider_user_id: string,         // Provider 端的用戶 ID
  activity_id: string,              // Provider 活動 ID
  firebase_uid?: string,            // 對應的 Firebase UID (如果已映射)

  // === 活動基本資訊 ===
  activity_type: string,            // running, cycling, etc.
  start_time_utc: Timestamp,        // 開始時間 (UTC)

  // === 處理狀態 ===
  processed: boolean,               // 是否已處理
  processing_attempts: number,      // 處理嘗試次數
  last_processing_attempt: Timestamp, // 最後處理嘗試時間

  // === 去重標記 ===
  is_duplicate: boolean,            // 是否為重複
  original_activity_id?: string,    // 原始活動 ID (如果是重複的)

  // === 時間戳 ===
  created_at: Timestamp,
  updated_at: Timestamp
}
```

#### Repository

**位置**: `core/database/repositories/provider_activity_repository.py`

**主要方法**:

```python
# 記錄活動
provider_activity_repository.record_activity(
    provider='strava',
    provider_user_id='strava_123',
    activity_id='12345678',
    data={
        'activity_type': 'running',
        'start_time_utc': datetime.now(timezone.utc)
    }
)

# 檢查是否重複
is_dup = provider_activity_repository.check_duplicate(
    provider='strava',
    activity_id='12345678'
)

# 標記為已處理
provider_activity_repository.mark_as_processed(
    provider='strava',
    activity_id='12345678'
)
```

---

### 17. audit_logs

**Collection Path**: `audit_logs`
**Document ID**: 自動生成

#### 文檔結構

```typescript
{
  // === 事件資訊 ===
  event_type: string,               // workout_created, plan_generated, user_registered, etc.
  event_source: string,             // api_service, webhook_service, scheduled_task

  // === 用戶資訊 ===
  uid?: string,                     // Firebase UID
  user_email?: string,              // 用戶 email

  // === 事件詳情 ===
  resource_type?: string,           // workout, training_plan, user, etc.
  resource_id?: string,             // 資源 ID
  action: string,                   // create, update, delete, sync

  // === 請求詳情 ===
  request_id?: string,              // 請求 ID
  ip_address?: string,              // IP 位址
  user_agent?: string,              // User Agent

  // === 結果 ===
  status: string,                   // success, failed, partial
  error_message?: string,           // 錯誤訊息 (如果失敗)

  // === 額外數據 ===
  metadata?: object,                // 任意額外數據

  // === 時間戳 ===
  created_at: Timestamp
}
```

#### 使用位置

無專用 repository，在各個服務中直接記錄。

#### 常用查詢

```python
# 查詢特定用戶的操作日誌
logs = (db.collection('audit_logs')
          .where('uid', '==', uid)
          .where('created_at', '>=', start_time)
          .order_by('created_at', direction=firestore.Query.DESCENDING)
          .limit(100)
          .stream())

# 查詢特定事件類型
logs = (db.collection('audit_logs')
          .where('event_type', '==', 'workout_created')
          .where('created_at', '>=', start_time)
          .stream())
```

#### 索引建議

```
複合索引:
- uid (ASC) + created_at (DESC)
- event_type (ASC) + created_at (DESC)
- resource_type (ASC) + resource_id (ASC)
```

---

### 18. backfill

**Collection Path**: `backfill/{provider}/items`
**Providers**: `strava`, `garmin`

#### 18.1 backfill/strava/items

**Document ID**: 自動生成的 backfill ID

**文檔結構**:

```typescript
{
  backfill_id: string,              // Backfill 任務 ID
  uid: string,                      // Firebase UID
  strava_user_id: string,           // Strava 用戶 ID

  // === 任務狀態 ===
  status: string,                   // pending, running, completed, failed
  progress: number,                 // 進度 (0-100)

  // === 回填範圍 ===
  start_date: string,               // 開始日期 (YYYY-MM-DD)
  end_date: string,                 // 結束日期 (YYYY-MM-DD)

  // === 統計 ===
  total_activities: number,         // 總活動數
  processed_activities: number,     // 已處理活動數
  failed_activities: number,        // 失敗活動數

  // === 錯誤記錄 ===
  errors?: string[],                // 錯誤訊息列表

  // === 時間戳 ===
  created_at: Timestamp,
  started_at?: Timestamp,           // 開始時間
  completed_at?: Timestamp,         // 完成時間
  updated_at: Timestamp
}
```

#### Repository

**Strava**: `core/database/repositories/strava_backfill_repository.py`
**Garmin**: `core/database/repositories/garmin_backfill_repository.py`

---

## 索引建議

### 必要複合索引

為了優化查詢性能，建議在 Firestore 中創建以下複合索引：

#### 1. workouts_v2_index
```
Collection: users/{uid}/workouts_v2_index

索引 1:
- start_time_utc: ASC
- provider: ASC

索引 2:
- start_time_utc: DESC
- activity_type: ASC

索引 3:
- matched_plan_id: ASC
- matched_day_index: ASC
```

#### 2. plan_race_run_weekly
```
Collection: plan_race_run_weekly

索引 1:
- uid: ASC
- overview_id: ASC
- week_of_plan: ASC

索引 2:
- overview_id: ASC
- week_of_plan: ASC
```

#### 3. audit_logs
```
Collection: audit_logs

索引 1:
- uid: ASC
- created_at: DESC

索引 2:
- event_type: ASC
- created_at: DESC

索引 3:
- resource_type: ASC
- resource_id: ASC
```

#### 4. training_readiness_cache
```
Collection: training_readiness_cache

索引 1:
- uid: ASC
- date: DESC

索引 2:
- uid: ASC
- expires_at: ASC
```

---

## CRUD 操作指南

### 基本操作模式

#### 1. 讀取操作 (Read)

```python
from core.infrastructure.firebase_init import db

# 單一文檔
doc_ref = db.collection('users').document(uid)
doc = doc_ref.get()

if doc.exists:
    data = doc.to_dict()
else:
    # 文檔不存在

# 子集合文檔
workout_ref = (db.collection('users')
                 .document(uid)
                 .collection('workouts_v2')
                 .document('providers')
                 .collection('strava')
                 .document(activity_id))

workout = workout_ref.get()
```

#### 2. 寫入操作 (Create/Update)

```python
# 創建新文檔 (自動生成 ID)
doc_ref = db.collection('users').document()
doc_ref.set({
    'uid': uid,
    'email': email,
    'created_at': firestore.SERVER_TIMESTAMP
})

# 創建文檔 (指定 ID)
db.collection('users').document(uid).set({
    'uid': uid,
    'email': email,
    'created_at': firestore.SERVER_TIMESTAMP
})

# 更新文檔
db.collection('users').document(uid).update({
    'display_name': '新名稱',
    'updated_at': firestore.SERVER_TIMESTAMP
})

# Upsert (不存在則創建，存在則更新)
db.collection('users').document(uid).set({
    'display_name': '新名稱',
    'updated_at': firestore.SERVER_TIMESTAMP
}, merge=True)
```

#### 3. 刪除操作 (Delete)

```python
# 刪除文檔
db.collection('users').document(uid).delete()

# 批次刪除 (需要分批)
batch = db.batch()

docs = db.collection('users').document(uid).collection('workouts_v2_index').limit(500).stream()
for doc in docs:
    batch.delete(doc.reference)

batch.commit()
```

#### 4. 查詢操作 (Query)

```python
# 簡單查詢
users = (db.collection('users')
           .where('language', '==', 'zh-TW')
           .stream())

# 複合查詢
workouts = (db.collection('users')
              .document(uid)
              .collection('workouts_v2_index')
              .where('start_time_utc', '>=', start_date)
              .where('start_time_utc', '<', end_date)
              .order_by('start_time_utc', direction=firestore.Query.DESCENDING)
              .limit(50)
              .stream())

# 分頁查詢
first_query = (db.collection('users')
                 .order_by('created_at')
                 .limit(10))

docs = first_query.stream()
last_doc = None
for doc in docs:
    last_doc = doc
    # 處理文檔

# 下一頁
next_query = (db.collection('users')
                .order_by('created_at')
                .start_after(last_doc)
                .limit(10))
```

#### 5. 批次操作 (Batch)

```python
# 批次寫入 (最多 500 個操作)
batch = db.batch()

# 新增
ref1 = db.collection('users').document('user1')
batch.set(ref1, {'name': 'User 1'})

# 更新
ref2 = db.collection('users').document('user2')
batch.update(ref2, {'name': 'Updated User 2'})

# 刪除
ref3 = db.collection('users').document('user3')
batch.delete(ref3)

# 提交
batch.commit()
```

#### 6. 交易操作 (Transaction)

```python
from google.cloud import firestore

@firestore.transactional
def update_user_vdot(transaction, user_ref, new_vdot):
    snapshot = user_ref.get(transaction=transaction)

    if not snapshot.exists:
        raise ValueError('User does not exist')

    current_vdot = snapshot.get('vdot')

    # 只有當新 VDOT 更高時才更新
    if new_vdot > current_vdot:
        transaction.update(user_ref, {
            'vdot': new_vdot,
            'updated_at': firestore.SERVER_TIMESTAMP
        })

# 使用交易
user_ref = db.collection('users').document(uid)
transaction = db.transaction()
update_user_vdot(transaction, user_ref, 50.5)
```

---

## 最佳實踐

### 1. 時區處理

⚠️ **關鍵規則**: 所有時間戳必須使用 UTC 儲存

```python
from datetime import datetime, timezone

# ✅ 正確: 使用 UTC
start_time_utc = datetime.now(timezone.utc)

# ✅ 正確: 轉換到 UTC
from utils.timezone_utils import convert_to_utc
user_local_time = datetime(2024, 3, 15, 18, 30)  # 用戶本地時間
start_time_utc = convert_to_utc(user_local_time, user_timezone='Asia/Taipei')

# ❌ 錯誤: 使用 naive datetime (沒有時區資訊)
start_time = datetime.now()  # 不要這樣做！
```

**顯示時轉換到用戶時區**:

```python
from utils.timezone_utils import convert_from_utc

# 從資料庫獲取 UTC 時間
workout_data = workout_ref.get().to_dict()
start_time_utc = workout_data['start_time_utc']

# 轉換到用戶時區顯示
user_local_time = convert_from_utc(start_time_utc, user_timezone='Asia/Taipei')
```

### 2. 數據驗證

⚠️ **使用 Pydantic Models 驗證數據**

```python
from data_models.workout_v2 import WorkoutV2Model

# ✅ 正確: 使用模型驗證
try:
    workout = WorkoutV2Model(**workout_data)
    # 數據有效，可以儲存
    workout_repository.save_workout_v2(uid, provider, activity_id, workout.dict())
except ValidationError as e:
    # 數據無效，處理錯誤
    logger.error(f"Validation error: {e}")

# ❌ 錯誤: 直接儲存未驗證的數據
db.collection('users').document(uid).collection('workouts_v2').document(id).set(workout_data)
```

### 3. 錯誤處理

```python
from google.cloud.exceptions import NotFound, AlreadyExists

try:
    doc = db.collection('users').document(uid).get()

    if not doc.exists:
        raise NotFound(f'User {uid} not found')

    data = doc.to_dict()

except NotFound as e:
    logger.error(f'Document not found: {e}')
    # 處理不存在的情況

except Exception as e:
    logger.error(f'Unexpected error: {e}')
    # 處理其他錯誤
```

### 4. 使用 Repository Pattern

⚠️ **永遠使用 Repository，不要直接操作 Firestore**

```python
# ✅ 正確: 使用 Repository
from core.database.repositories.user_repository import user_repository

user = user_repository.get_user(uid)
user_repository.update_user(uid, {'display_name': '新名稱'})

# ❌ 錯誤: 直接操作 Firestore
from core.infrastructure.firebase_init import db

user = db.collection('users').document(uid).get().to_dict()
db.collection('users').document(uid).update({'display_name': '新名稱'})
```

**原因**:
- Repository 提供統一的錯誤處理
- Repository 包含數據驗證邏輯
- Repository 確保一致的操作模式
- 方便測試 (可以 mock repository)

### 5. 敏感數據加密

⚠️ **Access Token 和 Refresh Token 必須加密儲存**

```python
from core.encryption.encryption_service import encryption_service

# ✅ 正確: 加密後儲存
encrypted_token = encryption_service.encrypt(access_token)
db.collection('users').document(uid).collection('provider_connections').document('strava').set({
    'access_token': encrypted_token,
    'refresh_token': encryption_service.encrypt(refresh_token)
})

# 讀取時解密
doc = db.collection('users').document(uid).collection('provider_connections').document('strava').get()
access_token = encryption_service.decrypt(doc.get('access_token'))

# ❌ 錯誤: 明文儲存
db.collection('users').document(uid).collection('provider_connections').document('strava').set({
    'access_token': access_token,  # 不要這樣做！
    'refresh_token': refresh_token
})
```

### 6. 查詢優化

```python
# ✅ 正確: 使用索引進行範圍查詢
workouts = (db.collection('users')
              .document(uid)
              .collection('workouts_v2_index')
              .where('start_time_utc', '>=', start_date)
              .where('start_time_utc', '<', end_date)
              .order_by('start_time_utc')
              .limit(50)
              .stream())

# ✅ 正確: 使用 limit 限制結果數量
users = db.collection('users').limit(100).stream()

# ❌ 錯誤: 查詢所有文檔
all_workouts = (db.collection('users')
                  .document(uid)
                  .collection('workouts_v2_index')
                  .stream())  # 可能返回數千個文檔！
```

### 7. 批次操作最佳化

```python
# ✅ 正確: 分批處理大量數據
def delete_all_workouts(uid, provider):
    batch_size = 500

    while True:
        docs = (db.collection('users')
                  .document(uid)
                  .collection('workouts_v2')
                  .document('providers')
                  .collection(provider)
                  .limit(batch_size)
                  .stream())

        deleted = 0
        batch = db.batch()

        for doc in docs:
            batch.delete(doc.reference)
            deleted += 1

        if deleted == 0:
            break

        batch.commit()

# ❌ 錯誤: 一次刪除所有文檔
docs = db.collection('users').document(uid).collection('workouts_v2').stream()
for doc in docs:
    doc.reference.delete()  # 可能超時或超過配額
```

### 8. 國際化 (i18n)

⚠️ **所有用戶可見字串必須使用 i18n**

```python
from core.i18n.i18n_service import i18n_service

# ✅ 正確: 使用 i18n
user_lang = user_data.get('language', 'zh-TW')
message = i18n_service.get_message(
    'training.rest_day',
    user_lang,
    date='2024-03-15'
)

# ❌ 錯誤: Hardcoded 字串
message = f'休息日: 2024-03-15'  # 不支援多語言
```

### 9. 審計日誌

⚠️ **重要操作必須記錄審計日誌**

```python
# ✅ 正確: 記錄重要操作
db.collection('audit_logs').add({
    'event_type': 'workout_deleted',
    'event_source': 'api_service',
    'uid': uid,
    'resource_type': 'workout',
    'resource_id': workout_id,
    'action': 'delete',
    'status': 'success',
    'created_at': firestore.SERVER_TIMESTAMP
})

# 包括錯誤情況
db.collection('audit_logs').add({
    'event_type': 'plan_generation_failed',
    'event_source': 'api_service',
    'uid': uid,
    'action': 'create',
    'status': 'failed',
    'error_message': str(e),
    'created_at': firestore.SERVER_TIMESTAMP
})
```

---

## Collection 使用統計

### 預估大小

| Collection | 預估文檔數 | 增長率 |
|-----------|----------|--------|
| **users** | 10K-100K | 穩定增長 |
| **users/{uid}/workouts_v2** | 100-10K per user | 每週 3-7 個 |
| **users/{uid}/workouts_v2_index** | 100-10K per user | 與 workouts_v2 相同 |
| **users/{uid}/health_daily** | 365-3650 per user | 每天 1 個 |
| **plan_race_run_overview** | 10K-100K | 穩定增長 |
| **plan_race_run_weekly** | 100K-1M | 每計畫 8-24 個 |
| **training_readiness_cache** | 100K-1M | 每用戶每天 1 個 |
| **audit_logs** | 1M-10M | 快速增長 |

### 查詢頻率

| 查詢類型 | 頻率 | 優化建議 |
|---------|------|---------|
| `users/{uid}` | 極高 (每次 API 請求) | 快取用戶基本資料 |
| `workouts_v2_index` 範圍查詢 | 高 (訓練列表頁面) | 使用複合索引 |
| `training_readiness_cache` | 高 (準備度頁面) | 檢查 expires_at 使用快取 |
| `plan_race_run_weekly` | 中 (週計畫頁面) | 快取當週計畫 |
| `health_daily` | 中 (健康數據頁面) | 按需查詢，不預加載 |
| `audit_logs` | 低 (審計和除錯) | 使用分頁查詢 |

---

## 相關文檔

### 代碼位置

- **Repositories**: `core/database/repositories/`
- **Data Models**: `data_models/`
- **Services**: `domains/*/`
- **API Endpoints**: `api/v1/`, `api/v2/`
- **Utilities**: `utils/`

### 架構文檔

- `COMPLETE_REFACTOR_SUMMARY.md` - 完整架構重構總結
- `LAZY_SINGLETON_QUICK_REF.md` - Singleton Pattern 快速參考
- `TESTING_GUIDELINES.md` - 測試指南
- `TRAINING_WEEKS_CALCULATION.md` - 訓練週次計算邏輯

---

## 附錄: Collection 完整清單

### 頂層 Collections

1. `users` - 用戶基本資料
2. `plan_race_run_overview` - 訓練計畫概覽
3. `plan_race_run_weekly` - 週訓練計畫
4. `training_readiness_cache` - 訓練準備度快取
5. `weekly_summary` - 週訓練摘要
6. `provider_activities` - Provider 活動記錄
7. `audit_logs` - 審計日誌
8. `backfill` - Backfill 任務

### 用戶子 Collections (users/{uid}/...)

1. `workouts_v2` - V2 訓練數據
2. `workouts_v2_index` - 訓練索引
3. `health_daily` - 每日健康數據
4. `targets` - 訓練目標
5. `plan_modifications` - 計畫修改記錄
6. `weekly_overview` - 週概覽
7. `agent_context` - AI Agent 上下文
8. `processing_results` - 處理結果
9. `processing_errors` - 處理錯誤
10. `provider_connections` - Provider 連接

---

**版本歷史**:

- **v1.0** (2025-11-19) - 初始版本，包含所有主要 Collections 的完整結構說明

---

**維護說明**:

- 當新增 Collection 時，請更新此文檔
- 當修改文檔結構時，請更新對應的 Data Models
- 當更改查詢模式時，請檢查索引是否需要更新

---

**聯絡資訊**:

如有任何問題或建議，請聯繫開發團隊或提交 Issue。
