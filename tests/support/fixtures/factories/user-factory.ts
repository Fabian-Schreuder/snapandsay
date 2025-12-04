export class UserFactory {
  private createdUsers: string[] = [];
  private faker: any;

  private async getFaker() {
    if (!this.faker) {
      const { faker } = await import('@faker-js/faker');
      this.faker = faker;
    }
    return this.faker;
  }

  async createUser(overrides = {}) {
    const faker = await this.getFaker();
    const user = {
      email: faker.internet.email(),
      name: faker.person.fullName(),
      password: faker.internet.password({ length: 12 }),
      ...overrides,
    };

    // API call to create user
    // Note: Adjust the endpoint to match your actual API
    let response;
    try {
      response = await fetch(`${process.env.API_URL}/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(user),
      });
    } catch (error) {
      console.warn('User creation API failed (network error), returning mock user');
      return { id: faker.string.uuid(), ...user };
    }

    if (!response.ok) {
        // Fallback for when API is not available or mocking is preferred
        console.warn('User creation API failed, returning mock user');
        return { id: faker.string.uuid(), ...user };
    }

    const created = await response.json();
    this.createdUsers.push(created.id);
    return created;
  }

  async cleanup() {
    // Delete all created users
    for (const userId of this.createdUsers) {
      try {
        await fetch(`${process.env.API_URL}/users/${userId}`, {
            method: 'DELETE',
        });
      } catch (e) {
          console.error(`Failed to cleanup user ${userId}`, e);
      }
    }
    this.createdUsers = [];
  }
}
