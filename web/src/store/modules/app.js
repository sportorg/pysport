const state = {
  isLoading: true
}

// getters
const getters = {
  isLoading: state => state.isLoading
}

const mutations = {
  setLoading (state, isLoading) {
    state.isLoading = isLoading
  }
}

const actions = {
}

export default {
  state,
  getters,
  mutations,
  actions
}
