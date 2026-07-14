<script setup>
import { computed, onBeforeUnmount, onMounted, ref, useId, watch } from 'vue'
import { CalendarDays, ChevronLeft, ChevronRight, X } from '@lucide/vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, required: true },
})
const emit = defineEmits(['update:modelValue'])
const root = ref(null)
const expanded = ref(false)
const calendarId = `date-picker-${useId()}`
const today = new Date()
const viewYear = ref(today.getFullYear())
const viewMonth = ref(today.getMonth())

const displayValue = computed(() => {
  const selected = parseDate(props.modelValue)
  return selected ? `${selected.year} 年 ${pad(selected.month + 1)} 月 ${pad(selected.day)} 日` : '年 / 月 / 日'
})

const calendarDays = computed(() => {
  const firstWeekday = (new Date(viewYear.value, viewMonth.value, 1).getDay() + 6) % 7
  const count = new Date(viewYear.value, viewMonth.value + 1, 0).getDate()
  const cells = Array.from({ length: firstWeekday }, (_, index) => ({ key: `before-${index}` }))
  for (let day = 1; day <= count; day += 1) {
    const key = formatDate(viewYear.value, viewMonth.value, day)
    cells.push({ key, day, selected: key === props.modelValue, today: key === formatDate(today.getFullYear(), today.getMonth(), today.getDate()) })
  }
  while (cells.length < 42) cells.push({ key: `after-${cells.length}` })
  return cells
})

watch(() => props.modelValue, syncView, { immediate: true })

function pad(value) {
  return String(value).padStart(2, '0')
}

function formatDate(year, month, day) {
  return `${year}-${pad(month + 1)}-${pad(day)}`
}

function parseDate(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value || '')
  return match ? { year: Number(match[1]), month: Number(match[2]) - 1, day: Number(match[3]) } : null
}

function syncView() {
  const selected = parseDate(props.modelValue)
  if (selected) {
    viewYear.value = selected.year
    viewMonth.value = selected.month
  }
}

function toggle() {
  if (!expanded.value) syncView()
  expanded.value = !expanded.value
}

function moveMonth(offset) {
  const next = new Date(viewYear.value, viewMonth.value + offset, 1)
  viewYear.value = next.getFullYear()
  viewMonth.value = next.getMonth()
}

function choose(day) {
  emit('update:modelValue', formatDate(viewYear.value, viewMonth.value, day))
  expanded.value = false
}

function chooseToday() {
  emit('update:modelValue', formatDate(today.getFullYear(), today.getMonth(), today.getDate()))
  expanded.value = false
}

function clear() {
  emit('update:modelValue', '')
  expanded.value = false
}

function handleOutside(event) {
  if (!root.value?.contains(event.target)) expanded.value = false
}

function handleKeydown(event) {
  if (event.key === 'Escape') expanded.value = false
}

onMounted(() => {
  document.addEventListener('pointerdown', handleOutside)
  document.addEventListener('keydown', handleKeydown)
})
onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleOutside)
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div ref="root" class="custom-date-picker">
    <button class="date-picker-trigger" type="button" :aria-label="label" :aria-expanded="expanded" :aria-controls="calendarId" @click="toggle">
      <span :class="{ placeholder: !modelValue }">{{ displayValue }}</span><CalendarDays :size="16" />
    </button>
    <div v-if="expanded" :id="calendarId" class="date-picker-popover" role="dialog" :aria-label="`${label}日期选择`">
      <header>
        <button type="button" title="上个月" @click="moveMonth(-1)"><ChevronLeft :size="17" /></button>
        <strong>{{ viewYear }} 年 {{ viewMonth + 1 }} 月</strong>
        <button type="button" title="下个月" @click="moveMonth(1)"><ChevronRight :size="17" /></button>
      </header>
      <div class="date-weekdays"><span v-for="weekday in ['一', '二', '三', '四', '五', '六', '日']" :key="weekday">{{ weekday }}</span></div>
      <div class="date-days">
        <template v-for="cell in calendarDays" :key="cell.key">
          <button v-if="cell.day" type="button" :class="{ selected: cell.selected, today: cell.today }" :aria-label="`${viewYear}年${viewMonth + 1}月${cell.day}日`" @click="choose(cell.day)">{{ cell.day }}</button>
          <span v-else></span>
        </template>
      </div>
      <footer><button class="today-command" type="button" @click="chooseToday">今天</button><button class="clear-date" type="button" title="清除日期" @click="clear"><X :size="15" /></button></footer>
    </div>
  </div>
</template>

<style scoped>
.custom-date-picker{position:relative;width:100%}.date-picker-trigger{width:100%;height:40px;display:flex;align-items:center;justify-content:space-between;gap:8px;padding:0 9px 0 11px;border:1px solid #d4dfde;background:#fbfdfc;color:#193e51;text-align:left;font-size:11px}.date-picker-trigger:hover,.date-picker-trigger[aria-expanded=true]{border-color:#43826f;background:#fff}.date-picker-trigger:focus-visible{outline:3px solid rgba(67,130,111,.18);outline-offset:1px}.date-picker-trigger .placeholder{color:#85969a;font-family:"DM Mono",monospace}.date-picker-trigger svg{flex:none;color:#43826f}.date-picker-popover{position:absolute;z-index:90;right:0;top:calc(100% + 7px);width:286px;padding:13px;border:1px solid #cbdad7;background:#fff;box-shadow:0 16px 34px rgba(15,48,62,.16)}.date-picker-popover header{height:34px;display:grid;grid-template-columns:32px 1fr 32px;align-items:center}.date-picker-popover header strong{text-align:center;color:#173d50;font:600 12px "DM Mono",monospace}.date-picker-popover header button,.clear-date{width:30px;height:30px;display:grid;place-items:center;border:0;background:transparent;color:#496974}.date-picker-popover header button:hover,.clear-date:hover{background:#edf5f1;color:#246653}.date-weekdays,.date-days{display:grid;grid-template-columns:repeat(7,32px);justify-content:space-between}.date-weekdays{margin:8px 0 4px}.date-weekdays span{height:24px;display:grid;place-items:center;color:#87979b;font-size:9px}.date-days{grid-template-rows:repeat(6,32px)}.date-days button,.date-days>span{width:32px;height:32px}.date-days button{border:0;background:transparent;color:#315360;font:500 10px "DM Mono",monospace}.date-days button:hover{background:#e7f2ed;color:#1f6653}.date-days button.today{box-shadow:inset 0 0 0 1px #8bb8ab}.date-days button.selected{background:#0b2f50;color:#fff;box-shadow:none}.date-picker-popover footer{height:34px;display:flex;align-items:end;justify-content:space-between;margin-top:6px;border-top:1px solid #e5ecea}.today-command{height:27px;padding:0;border:0;background:transparent;color:#2d6d5c;font-size:10px;font-weight:800}.clear-date{align-self:end}@media(max-width:600px){.date-picker-popover{width:min(286px,calc(100vw - 64px))}.date-weekdays,.date-days{grid-template-columns:repeat(7,minmax(28px,32px))}.date-days button,.date-days>span{width:100%}}
</style>
