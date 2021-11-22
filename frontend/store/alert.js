
export const state = () => ({
  content: '',
  color: '',
  level: '',
});
export const mutations = {
  showMessage(state, payload) {
    state.content = payload.content
    state.color = payload.color
    state.level = payload.level
  },
};
