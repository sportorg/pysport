<template>
  <div id="app">
    <router-view/>
  </div>
</template>

<script>
export default {
  name: 'App',
  created () {
    const updatedTime = () => {
      this.$http.get('updated_time?_=' + +(new Date())).then(res => {
        if (!res.data.is_alive) {
          this.$http.get('shutdown?_=' + +(new Date())).then()
        } else {
          if (res.data.updated_time !== this.$store.state.race.updatedTime) {
            this.$http.get('race').then(res => {
              this.$store.commit('setRace', res.data)
            })
            this.$store.commit('setUpdatedTime', res.data.updated_time)
          }
          setTimeout(updatedTime, 1000)
        }
      })
    }
    updatedTime()
  }
}
</script>

<style lang="scss">
  @import "sass/main";
</style>
