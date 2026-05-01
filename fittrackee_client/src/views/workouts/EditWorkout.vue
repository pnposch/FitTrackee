<template>
  <div id="edit-workout" class="view">
    <div class="container">
      <WorkoutEdition
        v-if="workoutData.workout.id"
        :authUser="authUser"
        :sports="sports"
        :workout="workoutData.workout"
        :loading="workoutData.loading"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
  import {
    computed,
    nextTick,
    onBeforeMount,
    onMounted,
    onUnmounted,
    ref,
    watch,
  } from 'vue'
  import type { ComputedRef, Ref } from 'vue'
  import { useRoute } from 'vue-router'

  import WorkoutEdition from '@/components/Workout/WorkoutEdition.vue'
  import useAuthUser from '@/composables/useAuthUser'
  import useSports from '@/composables/useSports'
  import { WORKOUTS_STORE } from '@/store/constants'
  import type { IWorkoutData } from '@/types/workouts'
  import { useStore } from '@/use/useStore'

  const route = useRoute()
  const store = useStore()

  const { authUser } = useAuthUser()
  const { sports } = useSports()

  const workoutData: ComputedRef<IWorkoutData> = computed(
    () => store.getters[WORKOUTS_STORE.GETTERS.WORKOUT_DATA]
  )
  const timer: Ref<ReturnType<typeof setTimeout> | undefined> = ref()

  function scrollTo(selector: string) {
    timer.value = setTimeout(() => {
      const element = document.getElementById(selector)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' })
      }
    }, 100)
  }

  watch(
    () => route.params.workoutId,
    async (newWorkoutId) => {
      if (!newWorkoutId) {
        store.commit(WORKOUTS_STORE.MUTATIONS.EMPTY_WORKOUT)
      }
    }
  )

  onBeforeMount(() => {
    store.dispatch(WORKOUTS_STORE.ACTIONS.GET_WORKOUT_DATA, {
      workoutId: route.params.workoutId,
    })
  })
  onMounted(() => {
    nextTick(() => {
      if (route.hash) {
        scrollTo(route.hash.replace('#', ''))
      }
    })
  })
  onUnmounted(() => {
    if (timer.value) {
      clearTimeout(timer.value)
    }
    store.commit(WORKOUTS_STORE.MUTATIONS.EMPTY_WORKOUT)
  })
</script>
