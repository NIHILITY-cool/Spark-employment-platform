<script setup>
import { computed, ref, useId, watch } from 'vue'
import { Check, ChevronDown, Search } from '@lucide/vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  options: { type: Array, default: () => [] },
  label: { type: String, required: true },
  placeholder: { type: String, default: '搜索并选择' },
  emptyLabel: { type: String, default: '全部' },
  allowEmpty: { type: Boolean, default: true },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'select'])
const query = ref('')
const expanded = ref(false)
const activeIndex = ref(-1)
const listId = `search-select-options-${useId()}`

const normalizedOptions = computed(() => [...new Set(props.options.map((item) => String(item || '').trim()).filter(Boolean))])
const matches = computed(() => {
  const term = query.value.trim().toLocaleLowerCase()
  return term ? normalizedOptions.value.filter((item) => item.toLocaleLowerCase().includes(term)) : normalizedOptions.value
})

watch(() => props.modelValue, (value) => {
  query.value = String(value || '')
}, { immediate: true })

function openPicker() {
  if (props.disabled) return
  expanded.value = true
  const selectedIndex = matches.value.indexOf(props.modelValue)
  activeIndex.value = selectedIndex >= 0 ? selectedIndex : (matches.value.length ? 0 : -1)
}

function closePicker() {
  expanded.value = false
  activeIndex.value = -1
}

function togglePicker() {
  if (expanded.value) closePicker()
  else openPicker()
}

function updateQuery() {
  if (query.value !== props.modelValue) emit('update:modelValue', '')
  openPicker()
}

function choose(value) {
  query.value = value
  emit('update:modelValue', value)
  emit('select', value)
  closePicker()
}

function clearSelection() {
  query.value = ''
  emit('update:modelValue', '')
  emit('select', '')
  closePicker()
}

function handleKeydown(event) {
  if (event.key === 'ArrowDown') {
    event.preventDefault()
    if (!expanded.value) openPicker()
    else activeIndex.value = Math.min(activeIndex.value + 1, matches.value.length - 1)
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    if (!expanded.value) openPicker()
    else activeIndex.value = Math.max(activeIndex.value - 1, 0)
  } else if (event.key === 'Enter' && expanded.value && activeIndex.value >= 0) {
    event.preventDefault()
    choose(matches.value[activeIndex.value])
  } else if (event.key === 'Escape') {
    closePicker()
  }
}
</script>

<template>
  <div class="search-select" @focusout="closePicker">
    <Search class="picker-search-icon" :size="17" aria-hidden="true" />
    <input
      v-model="query"
      class="picker-input"
      role="combobox"
      :aria-label="label"
      :aria-expanded="expanded"
      :aria-controls="listId"
      autocomplete="off"
      :placeholder="placeholder"
      :disabled="disabled"
      @focus="openPicker"
      @input="updateQuery"
      @keydown="handleKeydown"
    />
    <button class="picker-toggle" type="button" :aria-label="`展开${label}选项`" :disabled="disabled" @mousedown.prevent @click="togglePicker"><ChevronDown :size="17" /></button>
    <div v-if="expanded" :id="listId" class="picker-menu" role="listbox" :aria-label="`${label}匹配选项`">
      <div class="picker-menu-head"><span>{{ matches.length }} 个匹配选项</span><button v-if="allowEmpty" type="button" @mousedown.prevent @click="clearSelection">{{ emptyLabel }}</button></div>
      <div class="picker-options">
        <button v-for="(item, index) in matches" :key="item" class="picker-option" :class="{ active: index === activeIndex, selected: item === modelValue }" type="button" role="option" :aria-selected="item === modelValue" @mousedown.prevent @click="choose(item)">
          {{ item }}<Check v-if="item === modelValue" :size="14" aria-hidden="true" />
        </button>
        <p v-if="!matches.length" class="picker-empty">没有匹配的选项</p>
      </div>
    </div>
  </div>
</template>
