function getById (list, id) {
  if (id) {
    for (const obj of list) {
      if (obj.id === id) {
        return obj
      }
    }
  }
  return null
}

const state = {
  race: {},
  updatedTime: 0
}

// getters
const getters = {
  race: state => state.race,
  updated_time: state => state.updatedTime,
  getGroups: state => (state.race && state.race.groups) || []
}

// actions
const actions = {
}

// mutations
const mutations = {
  setRace (state, race) {
    for (const obj of race.persons) {
      obj.organization = getById(race.organizations, obj.organization_id)
      obj.group = getById(race.groups, obj.group_id)
    }
    for (const obj of race.results) {
      obj.person = getById(race.persons, obj.person_id)
    }
    for (const obj of race.groups) {
      obj.course = getById(race.courses, obj.course_id)
    }
    for (const itemName of ['groups', 'courses']) {
      race[itemName].sort((a, b) => {
        if (a.name.toUpperCase() < b.name.toUpperCase()) return -1
        if (a.name.toUpperCase() > b.name.toUpperCase()) return 1
        return 0
      })
    }
    state.race = race
  },
  setUpdatedTime (state, updatedTime) {
    state.updatedTime = updatedTime
  }
}

export default {
  state,
  getters,
  actions,
  mutations
}
