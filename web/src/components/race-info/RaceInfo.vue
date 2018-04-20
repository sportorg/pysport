<template>
  <div class="race-info">
    <b-container fluid>
      <b-row>
        <b-col cols="12">
          <b-button-group>
            <b-button v-for="group in $store.getters.getGroups"
                      :key="'b' + group.id"
                      @click="scrollToGroup(group.id)">{{group.name}}</b-button>
          </b-button-group>
          <b-badge v-if="$store.state.race.race" variant="primary">{{getCountPersons()}}</b-badge>
          <b-badge v-if="$store.state.race.race && getCountOutPersons()" variant="danger">{{getCountOutPersons()}}</b-badge>
        </b-col>
        <b-col cols="3">
          <b-card class="indentation-top" v-resize="70">
            <b-table small hover
                     :fields="['bib', 'surname', 'name', 'group', 'place']"
                     :items="getAllResults()">
              <template slot="surname" slot-scope="row">
                <span class="clickable" @click="scrollToPerson(row.item.id)">{{row.item.surname}}</span>
              </template>
              <template slot="name" slot-scope="row">
                <span class="clickable" @click="scrollToPerson(row.item.id)">{{row.item.name}}</span>
              </template>
              <template slot="group" slot-scope="row">
                <span v-if="row.item.group"
                      class="clickable"
                      @click="scrollToGroup(row.item.groupId)">{{row.item.group}}</span>
              </template>
            </b-table>
          </b-card>
        </b-col>
        <b-col cols="9">
          <b-row>
            <b-col cols="12">
              <div id="group-results" class="indentation-top" v-resize="70">
                <b-card :id="'group' + group.id"
                        class="indentation-bottom"
                        v-for="group in $store.getters.getGroups"
                        :key="group.id"
                        :title="group.name"
                        :sub-title="group.long_name">
                  <b-table responsive small hover
                           :fields="['n', 'bib', 'surname', 'name', 'year', 'org', 'place', 'result']"
                           :items="getResults(group)">
                    <template slot="n" slot-scope="row">
                      <b-button size="sm"
                                variant="outline-secondary"
                                v-if="row.item.bib !== void 0"
                                @click="row.toggleDetails">{{ row.detailsShowing ? '-' : '+'}}</b-button>
                    </template>
                    <template slot="surname" slot-scope="row">
                      <i :id="'person' + row.item.id"></i>{{row.item.surname}}
                    </template>
                    <template slot="org" slot-scope="row">
                      <span class="clickable" @click="selectOrg(row.item.org)">{{row.item.org}}</span>
                    </template>
                    <template slot="row-details" slot-scope="row">
                      <b-card>
                        <b-table v-if="row.item.data.type = 'ResultSportident'"
                                 :fields="['code', 'time']"
                                 :items="row.item.data.splits">
                          <template slot="time" slot-scope="row">
                            {{row.item.time|hhmmss}}
                          </template>
                        </b-table>
                      </b-card>
                    </template>
                  </b-table>
                </b-card>
              </div>
            </b-col>
          </b-row>
        </b-col>
      </b-row>
    </b-container>
  </div>
</template>

<script>
export default {
  name: 'race-info',
  data () {
    return {
      selectedOrg: '',
      selectedPerson: '',
      isRelay: false
    }
  },
  methods: {
    getResults (group) {
      this.isRelay = this.$store.state.race.race && this.$store.state.race.race.data.race_type === 3
      let results = []
      if (this.$store.state.race.race && this.$store.state.race.race.results) {
        for (const result of this.$store.state.race.race.results) {
          if (result.person && result.person.group && result.person.group.id === group.id) {
            const r = {
              id: result.person.id + '-' + result.id,
              created_at: result.created_at,
              bib: result.person.bib,
              surname: result.person.surname,
              name: result.person.name,
              year: result.person.birth_date ? (new Date(result.person.birth_date)).getFullYear() : '',
              org: (result.person.organization && result.person.organization.name) || '',
              startTime: result.start_time || result.person.start_time || 0,
              place: result.place || '',
              data: result,
              result: result.result,
              _showDetails: false
            }
            if (this.selectedOrg && this.selectedOrg === r.org) {
              r._rowVariant = 'success'
            }
            if (this.isNew(r.created_at * 1000)) {
              r._rowVariant = 'danger'
            }
            if (this.selectedPerson && this.selectedPerson === r.id) {
              r._rowVariant = 'warning'
              setTimeout(() => {
                r._rowVariant = ''
              }, 2000)
            }
            results.push(r)
          }
        }
      }
      results.sort((a, b) => {
        if (a.place === '') {
          return 1
        }
        if (b.place === '') {
          return -1
        }
        if (this.isRelay && a.place === b.place) {
          return ~~(a.bib / 1000) - ~~(b.bib / 1000)
        }
        return a.place - b.place
      })
      if (this.isRelay) {
        let prevBib = 0
        const resultsList = [...results]
        results = []
        for (const r of resultsList) {
          if (r.bib % 1000 !== prevBib) {
            results.push({_rowVariant: 'secondary', data: {}})
            prevBib = r.bib % 1000
          }
          results.push(r)
        }
      }
      return results
    },
    getAllResults () {
      const results = []
      if (this.$store.state.race.race && this.$store.state.race.race.results) {
        for (const result of this.$store.state.race.race.results) {
          if (result.person) {
            const r = {
              id: result.person.id + '-' + result.id,
              created_at: result.created_at,
              bib: result.person.bib,
              surname: result.person.surname,
              name: result.person.name,
              group: (result.person.group && result.person.group.name) || '',
              groupId: (result.person.group && result.person.group.id) || '',
              place: result.place || '',
              data: result
            }
            if (this.isNew(r.created_at * 1000)) {
              r._rowVariant = 'danger'
            }
            results.push(r)
          }
        }
      }
      results.sort((a, b) => {
        return b.created_at - a.created_at
      })
      return results
    },
    selectOrg (org) {
      if (this.selectedOrg === org) {
        this.selectedOrg = ''
      } else {
        this.selectedOrg = org
      }
    },
    scrollToGroup (id) {
      this.$scrollTo('#group' + id, 500, {container: '#group-results'})
    },
    scrollToPerson (id) {
      this.selectedPerson = id
      this.$scrollTo('#person' + id, 500, {container: '#group-results', offset: -window.innerHeight / 2})
    },
    isNew (timestamp) {
      return (+(new Date()) - timestamp) < (1000 * 30)
    },
    getCountPersons () {
      const race = this.$store.state.race.race
      return (race && race.persons && race.persons.length) || 0
    },
    getCountOutPersons () {
      const race = this.$store.state.race.race
      if (race && race.persons && race.results) {
        return race.persons.length - race.results.filter(elem => elem.person).length
      }
      return 0
    }
  }
}
</script>

<style lang="scss" scoped>
  .clickable {
    cursor: pointer;
  }
  .indentation-top {
    margin-top: 10px;
  }
  .indentation-bottom {
    margin-bottom: 10px;
  }
</style>
