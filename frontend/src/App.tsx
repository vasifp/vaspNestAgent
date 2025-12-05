/**
 * Main application component for vaspNestAgent dashboard.
 */

import React from 'react'
import { ApolloProvider } from '@apollo/client'
import { apolloClient } from './apollo/client'
import { Dashboard } from './components'
import './styles/index.css'

const App: React.FC = () => {
  return (
    <ApolloProvider client={apolloClient}>
      <Dashboard hours={24} adjustmentLimit={10} />
    </ApolloProvider>
  )
}

export default App
