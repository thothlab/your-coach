import { createSignal } from "solid-js";
import { getWebApp } from "./telegram";

export type Locale = "ru" | "en";

const STORAGE_KEY = "tb_locale";

function detectInitial(): Locale {
  // An explicit user choice (made via the in-app switcher) always wins.
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "ru" || stored === "en") return stored;
  } catch {
    // localStorage may be unavailable in some webviews — fall through.
  }
  // First launch: follow the user's Telegram language.
  const code = getWebApp()?.initDataUnsafe?.user?.language_code ?? "";
  return code.toLowerCase().startsWith("ru") ? "ru" : "en";
}

const [locale, setLocaleSignal] = createSignal<Locale>(detectInitial());

export { locale };

export function setLocale(next: Locale): void {
  try {
    localStorage.setItem(STORAGE_KEY, next);
  } catch {
    // Persistence is best-effort; the in-memory signal still updates.
  }
  setLocaleSignal(next);
}

type Dict = Record<string, string>;

const en: Dict = {
  "common.back": "← back",
  "common.save": "Save",
  "common.saving": "Saving…",
  "common.loading": "Loading…",
  "common.open": "Open",
  "common.confirm": "Confirm",
  "common.decline": "Decline",
  "common.send": "Send",
  "common.pick": "— pick —",
  "common.none": "— none —",
  "common.minutes": "{n} min",

  "app.loading": "Loading TrainBeat…",
  "error.title": "Something went wrong",
  "error.retry": "Try again",
  "error.notInTelegram": "Open this app inside Telegram.",

  "trainer.createGroup": "Create group",
  "trainer.newSession": "New session",
  "trainer.exercises": "Exercises",
  "trainer.workouts": "Workouts",
  "trainer.broadcast": "Broadcast",
  "trainer.groups": "Groups",
  "trainer.noGroups": 'No groups yet. Tap "Create group" above to make your first one.',
  "trainer.upcoming": "Upcoming (14 days)",
  "trainer.noSessions": "No scheduled sessions in the next 14 days.",
  "trainer.groupMeta": "({type}, {count} active)",

  "groupType.group": "Group",
  "groupType.personal": "Personal",
  "groupType.personalOption": "Personal (1 athlete)",

  "session.recurring": "recurring",
  "session.title": "Session #{id}",
  "session.confirmAttendance": "Confirm attendance",
  "session.sets": "Sets",
  "session.noSets": "No sets logged yet.",
  "session.exerciseTitle": "Exercise #{id}",
  "session.setLine": "set {n} · athlete #{id}",
  "session.repsSuffix": " · {reps} reps",
  "session.weightSuffix": " · {weight} kg",
  "session.secondsSuffix": " · {seconds} s",
  "session.addSet": "Add set",
  "session.promptExerciseId": "Exercise id?",
  "session.logByExerciseId": "Log a set by exercise id",

  "athlete.greeting": "Hi, {name}",
  "athlete.upcoming": "Upcoming sessions",
  "athlete.noSessions": "No upcoming sessions. Enjoy the rest day.",

  "field.name": "Name",
  "field.type": "Type",
  "field.unit": "Unit",
  "field.group": "Group",
  "field.workoutTemplateOpt": "Workout template (optional)",
  "field.start": "Start",
  "field.durationMin": "Duration (min)",
  "field.recurringWeekly": "Recurring weekly",
  "field.weekdays": "Weekdays",
  "field.sets": "Sets",
  "field.targetReps": "Reps per set",
  "field.targetWeight": "Weight, kg",
  "field.targetSeconds": "Time, sec",
  "field.message": "Message",

  "placeholder.groupName": "Monday strength",
  "placeholder.exerciseName": "Back squat",
  "placeholder.broadcast": "Bring water, see you at 7.",
  "placeholder.reps": "reps",
  "placeholder.kg": "kg",

  "validation.nameRequired": "Name is required",
  "validation.pickExerciseEvery": "Pick an exercise for every item",
  "validation.pickGroup": "Pick a group",
  "validation.pickStart": "Pick a start time",
  "validation.pickWeekday": "Pick at least one weekday",
  "validation.messageRequired": "Message text is required",

  "exercises.new": "+ New exercise",
  "exercises.newTitle": "New exercise",
  "exercise.mediaFile": "Photo or video (optional)",
  "exercise.mediaLink": "…or a link (YouTube / image)",
  "exercise.uploading": "Uploading…",
  "exercise.watch": "Watch in Telegram",
  "exercise.sent": "Sent to your chat ✓",
  "exercise.openLink": "Open link",
  "exercise.video": "Video",

  "unit.kg": "kg (weighted)",
  "unit.reps": "reps (bodyweight)",
  "unit.seconds": "seconds (timed)",
  "unit.meters": "meters (distance)",

  "workouts.title": "Workout templates",
  "workouts.new": "+ New template",
  "workouts.newTitle": "New workout template",
  "workouts.exerciseCount": "{n} exercises",
  "workouts.loadingExercises": "Loading exercises…",
  "workouts.items": "Items",
  "workouts.itemExercise": "Item {n} · Exercise",
  "workouts.removeItem": "Remove item",
  "workouts.addItem": "+ Add item",

  "broadcast.sent": "Sent to {count} member(s)",
  "broadcast.rateLimit": "Rate limit reached — try again later",
  "broadcast.charCount": "{len} / 4000",

  "invite.button": "Invite",
  "invite.title": "Invite to {group}",
  "invite.hint": "The athlete scans the QR or opens the link to join.",
  "invite.copy": "Copy link",
  "invite.copied": "Copied ✓",
  "invite.expires": "Valid until {date}",
  "invite.regenerate": "New link",

  "weekday.MO": "Mon",
  "weekday.TU": "Tue",
  "weekday.WE": "Wed",
  "weekday.TH": "Thu",
  "weekday.FR": "Fri",
  "weekday.SA": "Sat",
  "weekday.SU": "Sun",
};

const ru: Dict = {
  "common.back": "← назад",
  "common.save": "Сохранить",
  "common.saving": "Сохранение…",
  "common.loading": "Загрузка…",
  "common.open": "Открыть",
  "common.confirm": "Подтвердить",
  "common.decline": "Отклонить",
  "common.send": "Отправить",
  "common.pick": "— выбрать —",
  "common.none": "— нет —",
  "common.minutes": "{n} мин",

  "app.loading": "Загрузка TrainBeat…",
  "error.title": "Что-то пошло не так",
  "error.retry": "Повторить",
  "error.notInTelegram": "Откройте приложение внутри Telegram.",

  "trainer.createGroup": "Создать группу",
  "trainer.newSession": "Новая сессия",
  "trainer.exercises": "Упражнения",
  "trainer.workouts": "Тренировки",
  "trainer.broadcast": "Рассылка",
  "trainer.groups": "Группы",
  "trainer.noGroups": "Пока нет групп. Нажмите «Создать группу» выше, чтобы добавить первую.",
  "trainer.upcoming": "Ближайшие (14 дней)",
  "trainer.noSessions": "Нет запланированных сессий в ближайшие 14 дней.",
  "trainer.groupMeta": "({type}, активны: {count})",

  "groupType.group": "Группа",
  "groupType.personal": "Персональная",
  "groupType.personalOption": "Персональная (1 спортсмен)",

  "session.recurring": "повторяется",
  "session.title": "Сессия №{id}",
  "session.confirmAttendance": "Подтвердить участие",
  "session.sets": "Подходы",
  "session.noSets": "Подходы ещё не записаны.",
  "session.exerciseTitle": "Упражнение №{id}",
  "session.setLine": "подход {n} · спортсмен №{id}",
  "session.repsSuffix": " · {reps} повт.",
  "session.weightSuffix": " · {weight} кг",
  "session.secondsSuffix": " · {seconds} с",
  "session.addSet": "Добавить подход",
  "session.promptExerciseId": "ID упражнения?",
  "session.logByExerciseId": "Записать подход по ID упражнения",

  "athlete.greeting": "Привет, {name}",
  "athlete.upcoming": "Ближайшие сессии",
  "athlete.noSessions": "Нет ближайших сессий. Отдыхайте.",

  "field.name": "Название",
  "field.type": "Тип",
  "field.unit": "Единица",
  "field.group": "Группа",
  "field.workoutTemplateOpt": "Шаблон тренировки (необязательно)",
  "field.start": "Начало",
  "field.durationMin": "Длительность (мин)",
  "field.recurringWeekly": "Повтор еженедельно",
  "field.weekdays": "Дни недели",
  "field.sets": "Подходов",
  "field.targetReps": "Повторений в подходе",
  "field.targetWeight": "Вес, кг",
  "field.targetSeconds": "Время, сек",
  "field.message": "Сообщение",

  "placeholder.groupName": "Силовая по понедельникам",
  "placeholder.exerciseName": "Присед со штангой",
  "placeholder.broadcast": "Возьмите воду, встречаемся в 19:00.",
  "placeholder.reps": "повт.",
  "placeholder.kg": "кг",

  "validation.nameRequired": "Укажите название",
  "validation.pickExerciseEvery": "Выберите упражнение для каждого пункта",
  "validation.pickGroup": "Выберите группу",
  "validation.pickStart": "Укажите время начала",
  "validation.pickWeekday": "Выберите хотя бы один день недели",
  "validation.messageRequired": "Введите текст сообщения",

  "exercises.new": "+ Новое упражнение",
  "exercises.newTitle": "Новое упражнение",
  "exercise.mediaFile": "Фото или видео (необязательно)",
  "exercise.mediaLink": "…или ссылка (YouTube / картинка)",
  "exercise.uploading": "Загрузка…",
  "exercise.watch": "Смотреть в Telegram",
  "exercise.sent": "Отправлено в чат ✓",
  "exercise.openLink": "Открыть ссылку",
  "exercise.video": "Видео",

  "unit.kg": "кг (с весом)",
  "unit.reps": "повторения (свой вес)",
  "unit.seconds": "секунды (на время)",
  "unit.meters": "метры (дистанция)",

  "workouts.title": "Шаблоны тренировок",
  "workouts.new": "+ Новый шаблон",
  "workouts.newTitle": "Новый шаблон тренировки",
  "workouts.exerciseCount": "упражнений: {n}",
  "workouts.loadingExercises": "Загрузка упражнений…",
  "workouts.items": "Пункты",
  "workouts.itemExercise": "Пункт {n} · Упражнение",
  "workouts.removeItem": "Удалить пункт",
  "workouts.addItem": "+ Добавить пункт",

  "broadcast.sent": "Отправлено участникам: {count}",
  "broadcast.rateLimit": "Превышен лимит — попробуйте позже",
  "broadcast.charCount": "{len} / 4000",

  "invite.button": "Пригласить",
  "invite.title": "Пригласить в «{group}»",
  "invite.hint": "Спортсмен сканирует QR или открывает ссылку, чтобы вступить.",
  "invite.copy": "Скопировать ссылку",
  "invite.copied": "Скопировано ✓",
  "invite.expires": "Действует до {date}",
  "invite.regenerate": "Новая ссылка",

  "weekday.MO": "Пн",
  "weekday.TU": "Вт",
  "weekday.WE": "Ср",
  "weekday.TH": "Чт",
  "weekday.FR": "Пт",
  "weekday.SA": "Сб",
  "weekday.SU": "Вс",
};

const catalog: Record<Locale, Dict> = { ru, en };

export function t(key: string, params?: Record<string, string | number>): string {
  let s = catalog[locale()][key] ?? en[key] ?? key;
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      s = s.split(`{${k}}`).join(String(v));
    }
  }
  return s;
}
