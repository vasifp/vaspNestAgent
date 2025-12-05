/**
 * Apollo Client configuration with HTTP and WebSocket links.
 * 
 * Configures split link for routing queries to HTTP and subscriptions to WebSocket.
 * Requirements: 16.2
 */

import { ApolloClient, InMemoryCache, HttpLink, split } from '@apollo/client'
import { GraphQLWsLink } from '@apollo/client/link/subscriptions'
import { getMainDefinition } from '@apollo/client/utilities'
import { createClient } from 'graphql-ws'

// Get URLs from environment or use defaults
const httpUrl = import.meta.env.VITE_GRAPHQL_HTTP_URL || '/graphql'
const wsUrl = import.meta.env.VITE_GRAPHQL_WS_URL || 
  `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/graphql`

// HTTP link for queries and mutations
const httpLink = new HttpLink({
  uri: httpUrl,
})

// WebSocket link for subscriptions
const wsLink = new GraphQLWsLink(
  createClient({
    url: wsUrl,
    connectionParams: {
      // Add any auth tokens here if needed
    },
    retryAttempts: 5,
    shouldRetry: () => true,
    on: {
      connected: () => console.log('WebSocket connected'),
      closed: () => console.log('WebSocket closed'),
      error: (error) => console.error('WebSocket error:', error),
    },
  })
)

// Split link - route subscriptions to WebSocket, everything else to HTTP
const splitLink = split(
  ({ query }) => {
    const definition = getMainDefinition(query)
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    )
  },
  wsLink,
  httpLink
)

// Create Apollo Client
export const apolloClient = new ApolloClient({
  link: splitLink,
  cache: new InMemoryCache({
    typePolicies: {
      Query: {
        fields: {
          temperatureHistory: {
            // Replace existing readings with incoming ones
            merge(_, incoming) {
              return incoming
            },
          },
          adjustmentHistory: {
            merge(_, incoming) {
              return incoming
            },
          },
        },
      },
    },
  }),
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
    },
  },
})
